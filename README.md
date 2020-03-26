# Speedtest.net exporter for Prometheus
Speedtest.net offcial cli app - Prometheus Exporter

This is a small exporter built to allow Prometheus to scrape internet speedtests done with the official cli app from speedtest.net.

There are other exporters out there but they use a community done speedtest client that doesn't give accurate results

## Environment

This was done on an Ubuntu 20.04 on arm64 but any linux env should be fine.

## Components

This is a 3 piece exporter:

- The offical cli from Speedtest.net

**Instalation intructions:**

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

An adaptation of @pawadski script described [here] (https://apawel.me/exporting-prometheus-metrics-with-bash-scripts/)
