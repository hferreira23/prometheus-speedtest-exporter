#!/usr/bin/env python3
from prometheus_client.core import GaugeMetricFamily
from prometheus_client import make_wsgi_app, REGISTRY
import json
import subprocess
import shlex
import argparse
import random

# Parsing speedtest.net server list
parser = argparse.ArgumentParser(description='Process server list.')
parser.add_argument('-s', '--server-list-ids', dest='server_ids', action='store', help='Server list IDs(comma separated list)', required=False)
server_ids = vars(parser.parse_args())
server_list_ids = server_ids["server_ids"].split(',') if server_ids["server_ids"] is not None else []
collector = None

# Sets the /metrics
# / has a welcoming message
def speed_test(environ, start_fn):
    if environ['PATH_INFO'] == '/metrics':
        global collector
        if not collector:
            collector = CustomCollector(server_list_ids)
            REGISTRY.register(collector)
        return metrics_app(environ, start_fn)
    start_fn('200 OK', [])
    return [b'Hi there \\o\n\nMaybe you wanna go to /metrics!? :)']

# Create WSGI app
metrics_app = make_wsgi_app()

# Class that creates the Custom Collector
# Generates the speedtest metrics
class CustomCollector(object):
    def __init__(self, server_list_ids):
        self.server_list = server_list_ids

    def collect(self):
        if len(self.server_list) > 0:
            command = "speedtest -s " + random.choice(self.server_list) + " -f json --accept-license --accept-gdpr"
        else:
            command = "speedtest -f json --accept-license --accept-gdpr"
        args = shlex.split(command)
        res = subprocess.Popen(args, stdout=subprocess.PIPE)
        jsonS, _ = res.communicate()
        data = json.loads(jsonS)

        metrics = [
            ('latency_seconds', 'Latency', 'ping', '', 'latency'),
            ('latency_max_seconds', 'Latency Max', 'ping', '', 'high'),
            ('latency_min_seconds', 'Latency Min', 'ping', '', 'low'),
            ('jitter_seconds', 'Jitter', 'ping', '', 'jitter'),
            ('download_speed_bytes', 'Download Speed', 'download', '', 'bandwidth'),
            ('download_size_bytes', 'Download Size', 'download', '', 'bytes' ),
            ('download_latency_avg_seconds', 'Download Latency', 'download', 'latency', 'iqm' ),
            ('download_latency_max_seconds', 'Download Latency High', 'download', 'latency', 'high' ),
            ('download_latency_min_seconds', 'Download Latency Low', 'download', 'latency', 'low' ),
            ('download_latency_jitter_seconds', 'Download Latency Jitter', 'download', 'latency', 'jitter' ),
            ('upload_speed_bytes', 'Upload Speed', 'upload', '', 'bandwidth'),
            ('upload_size_bytes', 'Upload Size', 'upload', '', 'bytes'),
            ('upload_latency_avg_seconds', 'Upload Latency', 'upload', 'latency', 'iqm' ),
            ('upload_latency_max_seconds', 'Upload Latency High', 'upload', 'latency', 'high' ),
            ('upload_latency_min_seconds', 'Upload Latency Low', 'upload', 'latency', 'low' ),
            ('upload_latency_jitter_seconds', 'Upload Latency Jitter', 'upload', 'latency', 'jitter' ),
            ('packet_loss_ratio', 'Packet Loss', 'packetLoss', '', ''),
            ('timestamp_info', 'Time Stamp', 'timestamp', '', ''),
            ('servername_info', 'Server Name', 'servername', '', 'servername'),
            ('serverid_info', 'Server ID', 'serverid', '', 'id'),
            ('shareurl_info', 'Share URL', 'shareurl', '', 'url')
        ]

        for metric_name, metric_description, metric_type, metric_subtype, metric_value in metrics:
            if metric_type in ['servername', 'serverid', 'shareurl', 'timestamp']:
                metric = GaugeMetricFamily(
                    f'speedtest_{metric_name}',
                    metric_description,
                    labels=[f"speedtest_{metric_name}"]
                )

                label_value = None
                if metric_type == 'servername':
                    label_value = f"{data.get('server').get('host')}: {data.get('server').get('name')} - {data.get('server').get('location')}"
                elif metric_type == 'serverid':
                    label_value = str(data.get('server').get('id'))
                elif metric_type == 'shareurl':
                    label_value = data.get('result').get('url')
                elif metric_type == 'timestamp':
                    label_value = str(data.get('timestamp'))

                metric.add_metric([label_value], 1)

            elif metric_type == 'packetLoss':
                metric = GaugeMetricFamily(
                    f'speedtest_{metric_name}',
                    metric_description,
                    labels=['speedtest_metric']
                )

                metric.add_metric([metric_name], data.get(metric_type))

            elif metric_subtype == 'latency':
                metric = GaugeMetricFamily(
                    f'speedtest_{metric_name}',
                    metric_description,
                    labels=['speedtest_metric']
                )

                metric.add_metric([metric_name], data.get(metric_type).get(metric_subtype).get(metric_value))

            else:
                metric = GaugeMetricFamily(
                    f'speedtest_{metric_name}',
                    metric_description,
                    labels=['speedtest_metric']
                )

                metric.add_metric([metric_name], data.get(metric_type).get(metric_value))
            yield metric
