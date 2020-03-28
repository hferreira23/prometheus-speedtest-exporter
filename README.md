# Speedtest.net exporter for Prometheus
Speedtest.net offcial cli app - Prometheus Exporter

This is a small exporter built to allow Prometheus to scrape internet speedtests done with the official cli app from speedtest.net.

There are other exporters out there but they use a community done speedtest client that doesn't give accurate results

## Environment

This was done on an Ubuntu 20.04 on arm64 but any linux env should be fine.

## Components

This is a 4 piece exporter:

- The offical cli from Speedtest.net

**Instalation intructions:**

(Note: If the Ubuntu version is not listed on the supported ones use bionic as a reference)

```
sudo apt-get install gnupg1 apt-transport-https dirmngr
export INSTALL_KEY=379CE192D401AB61
# Ubuntu versions supported: xenial, bionic
# Debian versions supported: jessie, stretch, buster
export DEB_DISTRO=$(lsb_release -sc)
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys $INSTALL_KEY
echo "deb https://ookla.bintray.com/debian ${DEB_DISTRO} main" | sudo tee  /etc/apt/sources.list.d/speedtest.list
sudo apt-get update
# Other non-official binaries will conflict with Speedtest CLI
# Example how to remove using apt-get
# sudo apt-get remove speedtest-cli
sudo apt-get install speedtest
```
- speedtest-exporter.sh

A bash script adapted from [@pawadski](https://gitlab.com/pawadski) script described [here](https://apawel.me/exporting-prometheus-metrics-with-bash-scripts/). It basically runs the speedtest client and outputs to stdout in prometheus metric syntax.

- speedtest_exporter

A go webserver made by [@ricoberger](https://github.com/ricoberger) which exportes bash scripts for Prometheus.

The script_explorer binary in my repo was built for arm64 but if another arch is needed the source code can be found on Rico's [repo](https://github.com/ricoberger/script_exporter) along with instructions on how to build it.

The script_exporter loads its config from the config.yml. Adapt to your scenario accordantly. By default runs on port 9469.

config.yml example:
```
tls:
  enabled: false
  crt: server.crt
  key: server.key

basicAuth:
  enabled: false
  username: admin
  password: admin

bearerAuth:
  enabled: false
  signingKey: my_secret_key

scripts:
  - name: speedtest
    script: ./speedtest-exporter.sh
```

- speedtest_exporter.service (systemd file service file)

Self explanatory. Systemd service file to start/stop/restart the exporter.

## Puting it all together

* Install speedtest client using instructions above

* Deploy the speedtest-exporter.sh and script_exporter to a directory of your choosing (it's easier if the directory is by default on the $PATH of all users). I used:
```
/usr/local/bin/speedtest-exporter.sh
/usr/local/bin/speedtest_exporter
```

* Deploy config.yml to a diretory of your choosing (make sure the systemd service reflets that change). I used:
```
/etc/speedtest_exporter/config.yml
```

* Deploy the systemctl service file to:
```
/etc/systemd/system/speedtest_exporter.service
```

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

* Enable and start the service
```
systemctl daemon-reload
systemctl enable speedtest-exporter.service
systemctl start speedtest-exporter.service
```

* Restart Prometheus to reload new config

## Grafana

My grafana dashboard is available [here](https://grafana.com/grafana/dashboards/11988/)

Or the speedtest-exporter.json present in this repo can be used instead.

## Ansible

For those who use Ansible I added the role to setup all of this (with the exception of prometheus and Grafana dashboard). Just copy/move:
```
speedtest-exporter.sh
speedtest_exporter
speedtest_exporter.service
config.yml
```

to the files directory inside the role.
