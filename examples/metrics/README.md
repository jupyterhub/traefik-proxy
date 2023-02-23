# -p 9090:9090 \

docker run \
 -p 9090:9090 \
 -v $PWD/prometheus.yml:/etc/prometheus/prometheus.yml \
 prom/prometheus
