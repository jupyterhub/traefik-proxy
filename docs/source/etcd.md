# Using traefik-proxy with etcd

[etcd](https://coreos.com/etcd/)
is a distributed key-value store.
This is the choice to use when using jupyterhub-traefik-proxy
in a distributed setup, such as a Kubernetes cluster,
e.g. with multiple traefik proxy instances.

TODO:

- install traefik, etcd
- Enable traefik-etcd in jupyterhub_config.py
- explain required configuration of etcd (credentials, url)
- explain required traefik configuration
  when traefik is managed outside (e.g. zero-to-jupyterhub)
- step-by-step example setup
