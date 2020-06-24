#!/bin/bash
# printMetric name description type value
function printMetric {
    echo "# HELP $1 $2"
    echo "# TYPE $1 $3"
    echo "$1$5 $4"
}

while IFS=$'\t' read -r servername serverid latency jitter packetloss download upload downloadedbytes uploadedbytes shareurl; do
    printMetric "speedtest_servername_info" "Server Name" "gauge" "1" "{speedtest_servername=\"$servername\"}"
    printMetric "speedtest_serverid_info" "Server ID" "gauge" "1" "{speedtest_serverid=\"$serverid\"}"
    printMetric "speedtest_latency_seconds" "Latency" "gauge" "$latency"
    printMetric "speedtest_jittter_seconds" "Jitter" "gauge" "$jitter"
    printMetric "speedtest_download_bytes" "Download Speed" "gauge" "$download"
    printMetric "speedtest_upload_bytes" "Upload Speed" "gauge" "$upload"
    printMetric "speedtest_downloadedbytes_bytes" "Downloaded Bytes" "gauge" "$downloadedbytes"
    printMetric "speedtest_uploadedbytes_bytes" "Uploaded Bytes" "gauge" "$uploadedbytes"
    printMetric "speedtest_shareurl_info" "Share URL" "gauge" "1" "{speedtest_shareurl=\"$shareurl\"}"
done < <(/usr/bin/speedtest -f tsv)