#!/bin/sh
#CHP methods performance
python3 -m performance.check_perf --measure=methods --proxy=CHP --iterations=4 --routes_number=500 --concurrent --output=./results/chp_methods_concurrent.csv
# TomlProxy methods performance - throttle = 2s
python3 -m performance.check_perf --measure=methods --proxy=TomlProxy --iterations=4 --routes_number=500 --concurrent --output=./results/toml_methods_concurrent.csv
# EtcdProxy methods performance - throttle = 2s
#start etcd:
etcd &>/dev/null &
python3 -m performance.check_perf --measure=methods --proxy=EtcdProxy --iterations=4 --routes_number=500 --concurrent --output=./results/etcd_methods_concurrent.csv
#stop etcd:
pkill etcd
-rf default.etcd/

# Throughput:
#start backends:
python3 ./performance/dummy_http_server.py 9001 & #port 9001
python3 ./performance/dummy_ws_server.py & #port 9000

python3 -m performance.check_perf --measure=http_throughput_small --proxy=CHP --concurrent_requests_number=10 --backend_port=9001 --output=./results/http_throughput_small.csv
python3 -m performance.check_perf --measure=http_throughput_small --proxy=TomlProxy --concurrent_requests_number=10 --backend_port=9001 --output=./results/http_throughput_small.csv
#start etcd:
etcd &>/dev/null &
python3 -m performance.check_perf --measure=http_throughput_small --proxy=EtcdProxy --concurrent_requests_number=10 --backend_port=9001 --output=./results/http_throughput_small.csv
#stop etcd:
pkill etcd
-rf default.etcd/

python3 -m performance.check_perf --measure=http_throughput_large --proxy=CHP --concurrent_requests_number=10 --backend_port=9001 --output=./results/http_throughput_large.csv
python3 -m performance.check_perf --measure=http_throughput_large --proxy=TomlProxy --concurrent_requests_number=10 --backend_port=9001 --output=./results/http_throughput_large.csv
#start etcd:
etcd &>/dev/null &
python3 -m performance.check_perf --measure=http_throughput_large --proxy=EtcdProxy --concurrent_requests_number=10 --backend_port=9001 --output=./results/http_throughput_large.csv
#stop etcd:
pkill etcd
-rf default.etcd/
 
python3 -m performance.check_perf --measure=ws_throughput --proxy=CHP --concurrent_requests_number=10 --output=./results/ws_throughput.csv
python3 -m performance.check_perf --measure=ws_throughput --proxy=TomlProxy --concurrent_requests_number=10 --output=./results/ws_throughput.csv
#start etcd:
etcd &>/dev/null &
python3 -m performance.check_perf --measure=ws_throughput --proxy=EtcdProxy --concurrent_requests_number=10 --output=./results/ws_throughput.csv
#stop etcd:
pkill etcd
-rf default.etcd/
