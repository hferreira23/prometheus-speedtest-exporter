FROM python:3.13-slim AS base

FROM base AS builder

RUN apt update && \
    apt install gcc -y

RUN python3 -m pip install  --prefix="/build" prometheus_client uwsgi

FROM base

RUN apt update && \
    apt install curl bash -y && \
    curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | bash && \
    apt install speedtest -y && \
    mkdir -p /app/speedtest_exporter && \
    rm -rf /var/cache/* && \
    sync

COPY --from=builder /build /usr/local
COPY speedtest_exporter.ini /app/speedtest_exporter/speedtest_exporter.ini
COPY speedtest_exporter.py /app/speedtest_exporter/speedtest_exporter.py

EXPOSE 9469

CMD ["uwsgi", "--ini", "/app/speedtest_exporter/speedtest_exporter.ini"]
