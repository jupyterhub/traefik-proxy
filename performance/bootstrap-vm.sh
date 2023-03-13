#!/bin/bash
set -exuo pipefail
# script to setup a VM to prepare for running benchmarks
# installs python, this package, etcd, consul, traefik, chp

# gcloud compute instances create proxy-bench \
    # --project=binderhub-288415 \
    # --zone=us-central1-a \
    # --machine-type=n1-standard-96 \
    # --network-interface=network-tier=PREMIUM,subnet=default \
    # --no-restart-on-failure \
    # --maintenance-policy=TERMINATE \
    # --provisioning-model=SPOT \
    # --instance-termination-action=STOP \
    # --max-run-duration=18000s \
    # --create-disk=auto-delete=yes,boot=yes,device-name=proxy-bench,image=projects/ubuntu-os-cloud/global/images/ubuntu-2204-jammy-v20230302,mode=rw,size=10,type=projects/binderhub-288415/zones/us-central1-a/diskTypes/pd-balanced

apt update
apt -y install etcd python3 python3-pip nodejs npm
npm install --global configurable-http-proxy
python3 -m pip install -e .. -r requirements.txt

# install consul
if [[ -z $(which consul) ]]; then
  wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
  echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
  apt update && apt install consul
fi

# install  traefik
python3 -m jupyterhub_traefik_proxy.install --output /usr/local/bin
