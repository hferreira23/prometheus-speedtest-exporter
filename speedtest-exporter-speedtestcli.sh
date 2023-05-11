#!/bin/bash
# printMetric name description type value
function printMetric {
    echo "# HELP $1 $2"
    echo "# TYPE $1 $3"
    echo "$1$5 $4"
}

# Execute the speedtest command and save the output to a variable
speedtest_output=$(speedtest-cli --csv)

# Iterate over each line of the speedtest output and process the metrics
echo "$speedtest_output" | while IFS=',' read -r serverid servername timestamp latency jitter packetloss download upload download_bytes upload_bytes share_url; do
    # Print out the metrics using the printMetric function
    printMetric "speedtest_latency_seconds" "Latency" "gauge" "$latency"
    printMetric "speedtest_jitter_seconds" "Jitter" "gauge" "$jitter"
    printMetric "speedtest_download_bytes" "Download Speed" "gauge" "$download"
    printMetric "speedtest_upload_bytes" "Upload Speed" "gauge" "$upload"
    printMetric "speedtest_downloadedbytes_bytes" "Downloaded Bytes" "gauge" "$download_bytes"
    printMetric "speedtest_uploadedbytes_bytes" "Uploaded Bytes" "gauge" "$upload_bytes"
done
