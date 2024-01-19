# JupyterHub Traefik Proxy

An implementation of the JupyterHub proxy api with [traefik](https://traefik.io): an extremely lightweight, portable reverse proxy implementation that supports load balancing and can configure itself automatically and dynamically.

## Why traefik?

Currently, the **default** proxy implementation for JupyterHub is [configurable-http-proxy](https://github.com/jupyterhub/configurable-http-proxy) (CHP), which stores the routing table in-memory. This might be the best approach in most cases, but because you can only run a single copy of the proxy at a time, it has its limitations when used in dynamic large scale systems.

When using a proxy implementation based on traefik, you can run multiple instances of traefik by using a distributed key-value store like [redis](https://redis.io) to store the routing table. This makes the proxy **highly available** and improves the scalability and stability of the system.
Moreover, traefik offers _HTTPS_ support through a straight-forward [ACME (Let's Encrypt)](https://docs.traefik.io/configuration/acme) configuration.

There are three versions for the proxy, depending on how traefik stores the routes:

- _for_ **smaller**, _single-node deployments_, use plain files:
  - TraefikFileProviderProxy
- _for_ **distributed** _setups_, use a key-value store:
  - TraefikRedisProxy (recommended)
  - TraefikEtcdProxy
  - TraefikConsulProxy (deprecated)

### Picking a key-value backend

If you are planning to run a with a key-value backend, you'll have to pick which one.
The key-value store implementations are fairly equivalent.
If you already have a key-value store running, you can stick with that.
We currently recommend [redis](redis) as the default if you don't have specific reasons to pick another one.

The health of Python APIs for each key-value store is _very_ inconsistent.
As of January 2024, it appears that redis is the only key-value store supported by traefik with a well-supported Python client.
Consul support is deprecated, given its current client situation.
Etcd is in a slightly better situation, but may end up deprecated as well, given that we now have a redis implementation.
As a result, we recommend using redis.

etcd has one benefit over redis of being a single binary file to download and install,
while redis is typically installed via `apt`, etc.
But in most cases where traefik will actually be used with a key-value store, the store backend is very likely to be run in its own container where installation differences don't really come up.

## Contents

### Installation Guide

```{toctree}
:maxdepth: 2

install
```

### Getting Started

```{toctree}
:maxdepth: 1

https
file
redis
etcd
consul
```

### API Reference

```{toctree}
:maxdepth: 3

api/index
changelog
details
```

## Indices and tables

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`
