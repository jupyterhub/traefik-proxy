#!/bin/sh
#CHP methods performance
python3 -m performance.check_perf --measure=methods --proxy=CHP --iterations=2 --routes_number=500 --sequential --output=./results/chp_methods_sequential.csv
# FileProxy methods performance - run with throttle = 0s
python3 -m performance.check_perf --measure=methods --proxy=FileProxy --iterations=2 --routes_number=500 --sequential --output=./results/toml_methods_sequential.csv
# EtcdProxy methods performance - run with throttle = 0s
#start etcd:
etcd &> /dev/null &
python3 -m performance.check_perf --measure=methods --proxy=EtcdProxy --iterations=2 --routes_number=500 --sequential --output=./results/etcd_methods_sequential.csv
#stop etcd:
pkill etcd
-rf default.etcd/

