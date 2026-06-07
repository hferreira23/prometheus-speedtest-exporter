#!/usr/bin/env python3
"""Prometheus exporter for speedtest.net metrics."""

import argparse
import json
import logging
import random
import subprocess
from collections.abc import Callable, Iterator

from prometheus_client import REGISTRY, make_wsgi_app
from prometheus_client.core import GaugeMetricFamily

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

SPEEDTEST_TIMEOUT = 120

# (name, description, metric_type, subtype, value_key, scale)
METRICS = [
    ("latency_seconds", "Latency", "ping", "", "latency", 1e-3),
    ("latency_max_seconds", "Latency Max", "ping", "", "high", 1e-3),
    ("latency_min_seconds", "Latency Min", "ping", "", "low", 1e-3),
    ("jitter_seconds", "Jitter", "ping", "", "jitter", 1e-3),
    ("download_speed_bytes", "Download Speed", "download", "", "bandwidth", 1),
    ("download_size_bytes", "Download Size", "download", "", "bytes", 1),
    ("download_latency_avg_seconds", "Download Latency Avg", "download", "latency", "iqm", 1e-3),
    ("download_latency_max_seconds", "Download Latency High", "download", "latency", "high", 1e-3),
    ("download_latency_min_seconds", "Download Latency Low", "download", "latency", "low", 1e-3),
    ("download_latency_jitter_seconds", "Download Latency Jitter", "download", "latency", "jitter", 1e-3),
    ("upload_speed_bytes", "Upload Speed", "upload", "", "bandwidth", 1),
    ("upload_size_bytes", "Upload Size", "upload", "", "bytes", 1),
    ("upload_latency_avg_seconds", "Upload Latency Avg", "upload", "latency", "iqm", 1e-3),
    ("upload_latency_max_seconds", "Upload Latency High", "upload", "latency", "high", 1e-3),
    ("upload_latency_min_seconds", "Upload Latency Low", "upload", "latency", "low", 1e-3),
    ("upload_latency_jitter_seconds", "Upload Latency Jitter", "upload", "latency", "jitter", 1e-3),
    ("packet_loss_ratio", "Packet Loss", "packetLoss", "", "", 1),
    ("timestamp_info", "Time Stamp", "timestamp", "", "", 1),
    ("servername_info", "Server Name", "servername", "", "", 1),
    ("serverid_info", "Server ID", "serverid", "", "", 1),
    ("shareurl_info", "Share URL", "shareurl", "", "", 1),
]

INFO_METRIC_TYPES = frozenset({"servername", "serverid", "shareurl", "timestamp"})


class SpeedtestError(Exception):
    """Raised when the speedtest command fails or returns invalid output."""


class CustomCollector:
    def __init__(self, server_list: list[str]) -> None:
        self.server_list = server_list

    def _run_speedtest(self) -> dict:
        cmd = ["speedtest", "-f", "json", "--accept-license", "--accept-gdpr"]
        if self.server_list:
            cmd += ["-s", random.choice(self.server_list)]

        logger.info("Running: %s", " ".join(cmd))
        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=SPEEDTEST_TIMEOUT,
                check=True,
            )
        except subprocess.TimeoutExpired as exc:
            raise SpeedtestError(
                f"speedtest timed out after {SPEEDTEST_TIMEOUT}s"
            ) from exc
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode(errors="replace").strip()
            raise SpeedtestError(
                f"speedtest exited with code {exc.returncode}: {stderr}"
            ) from exc

        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise SpeedtestError(f"Failed to parse speedtest JSON: {exc}") from exc

    @staticmethod
    def _nested_get(data: dict, *keys: str) -> object | None:
        obj = data
        for key in keys:
            if not isinstance(obj, dict):
                return None
            obj = obj.get(key)
        return obj

    def collect(self) -> Iterator[GaugeMetricFamily]:
        scrape_error = GaugeMetricFamily(
            "speedtest_scrape_error",
            "1 if the last speedtest scrape failed, 0 otherwise",
        )
        try:
            data = self._run_speedtest()
        except SpeedtestError as exc:
            logger.error("Speedtest scrape failed: %s", exc)
            scrape_error.add_metric([], 1)
            yield scrape_error
            return

        scrape_error.add_metric([], 0)
        yield scrape_error

        for metric_name, description, metric_type, subtype, value_key, scale in METRICS:
            full_name = f"speedtest_{metric_name}"
            if metric_type in INFO_METRIC_TYPES:
                metric = GaugeMetricFamily(full_name, description, labels=[full_name])
                if metric_type == "servername":
                    label_value = (
                        f"{self._nested_get(data, 'server', 'host')}: "
                        f"{self._nested_get(data, 'server', 'name')} - "
                        f"{self._nested_get(data, 'server', 'location')}"
                    )
                elif metric_type == "serverid":
                    label_value = str(self._nested_get(data, "server", "id") or "")
                elif metric_type == "shareurl":
                    label_value = str(self._nested_get(data, "result", "url") or "")
                else:
                    label_value = str(data.get("timestamp", ""))
                metric.add_metric([label_value], 1)
            else:
                metric = GaugeMetricFamily(full_name, description, labels=["speedtest_metric"])
                if metric_type == "packetLoss":
                    value = data.get("packetLoss")
                elif subtype == "latency":
                    value = self._nested_get(data, metric_type, subtype, value_key)
                else:
                    value = self._nested_get(data, metric_type, value_key)

                if value is not None:
                    metric.add_metric([metric_name], float(value) * scale)

            yield metric


def build_wsgi_app(server_list: list[str]) -> Callable:
    REGISTRY.register(CustomCollector(server_list))
    _metrics_app = make_wsgi_app()

    def app(environ, start_fn):
        if environ["PATH_INFO"] == "/metrics":
            return _metrics_app(environ, start_fn)
        start_fn("200 OK", [("Content-Type", "text/plain")])
        return [b"Hi there \\o\n\nMaybe you wanna go to /metrics!? :)"]

    return app


def parse_server_list() -> list[str]:
    parser = argparse.ArgumentParser(description="Prometheus exporter for speedtest.net")
    parser.add_argument(
        "-s",
        "--server-list-ids",
        dest="server_ids",
        help="Comma-separated list of speedtest server IDs to randomly select from",
        required=False,
    )
    args = parser.parse_args()
    return args.server_ids.split(",") if args.server_ids else []


application = build_wsgi_app(parse_server_list())
