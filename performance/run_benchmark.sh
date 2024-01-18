#!/bin/sh
# no -e to allow data generation, only losing failed results
set -exuo pipefail

echo $0
cd $(dirname "$0")
export PYTHONPATH="$PWD/.."

iterations=${iterations:-3}
routes=${routes:-500}

proxies="${proxies:-chp file etcd consul redis}"
# add/remove route API performance
for proxy in $proxies; do
  for concurrency in 1 10 20 50; do
    python3 -m performance.check_perf methods --proxy=$proxy --iterations=$iterations --concurrency=$concurrency --routes=$routes --output=./results/${proxy}-methods.csv
  done
done


# Throughput:

for metric in http_throughput_small http_throughput_large ws_throughput_small ws_throughput_large; do
  for concurrency in 1 10 20 50; do
    for proxy in chp file; do
    # no reason to use other config backends when testing throughput
      sleep 5
      python3 check_perf.py $metric --proxy=$proxy --iterations=$iterations --concurrency=$concurrency --output=./results/${proxy}-${metric}.csv
    done
  done
done
