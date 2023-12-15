# Speedtest.net exporter for Prometheus
Speedtest.net offcial cli app - Prometheus Exporter

This is a small exporter built to allow Prometheus to scrape internet speedtests done with the official cli app from speedtest.net.

There are other exporters out there but they use a community done speedtest client that doesn't give accurate results

## Environment



## Puting it all together

* Install speedtest client using instructions above

* Add relevant config to prometheus.yml. Example:
```
  - job_name: 'Speedtest'
    scrape_interval: 30m
    scrape_timeout: 1m
    metrics_path: /probe
    params:
      script: [speedtest]
    static_configs:
      - targets:
        - 192.168.1.2:9469
```

* Restart Prometheus to reload new config

## Grafana

My grafana dashboard is available [here](https://grafana.com/grafana/dashboards/11988/)

Or the speedtest-exporter.json present in this repo can be used instead.
