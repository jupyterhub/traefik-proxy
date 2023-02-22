
# JupyterHub Traefik Proxy

[![Documentation build status](https://img.shields.io/readthedocs/jupyterhub-traefik-proxy?logo=read-the-docs)](https://jupyterhub-traefik-proxy.readthedocs.org/en/latest/)
[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/jupyterhub/traefik-proxy/Run%20tests?logo=github)](https://github.com/jupyterhub/traefik-proxy/actions)
[![CircleCI build status](https://img.shields.io/circleci/build/github/jupyterhub/jupyterhub?logo=circleci)](https://circleci.com/gh/jupyterhub/jupyterhub)
[![Latest PyPI version](https://img.shields.io/pypi/v/jupyterhub-traefik-proxy?logo=pypi)](https://pypi.python.org/pypi/jupyterhub-traefik-proxy)
[![GitHub](https://img.shields.io/badge/issue_tracking-github-blue?logo=github)](https://github.com/jupyterhub/traefik-proxy/issues)
[![Discourse](https://img.shields.io/badge/help_forum-discourse-blue?logo=discourse)](https://discourse.jupyter.org/c/jupyterhub)
[![Gitter](https://img.shields.io/badge/social_chat-gitter-blue?logo=gitter)](https://gitter.im/jupyterhub/jupyterhub)

When JupyterHub starts a server for a user, it will _dynamically configure a
proxy server_ so that accessing `jupyterhub.example.com/user/<user>` routes to
the individual Jupyter server. This project contains what JupyterHub need to
dynamically configure the routes of a [traefik](https://traefik.io) proxy
server! There are three implementations of the [JupyterHub proxy
API](https://jupyterhub.readthedocs.io/en/stable/reference/proxy.html),
depending on how traefik store its routing configuration.

For **smaller**, single-node deployments:

* TraefikFileProviderProxy

For **distributed** setups:

* TraefikEtcdProxy
* TraefikConsulProxy

## Installation

The [documentation](https://jupyterhub-traefik-proxy.readthedocs.io) contains a
[complete installation
guide](https://jupyterhub-traefik-proxy.readthedocs.io/en/latest/install.html)
with examples for the three different implementations.

* [For TraefikFileProviderProxy](https://jupyterhub-traefik-proxy.readthedocs.io/en/latest/file.html#example-setup)
* [For TraefikEtcdProxy](https://jupyterhub-traefik-proxy.readthedocs.io/en/latest/etcd.html#example-setup)
* [For TraefikConsulProxy](https://jupyterhub-traefik-proxy.readthedocs.io/en/latest/consul.html#example-setup)

## Docker Compose

A fully functional `docker-compose` example environment is included in the
[examples](examples/docker-compose) directory. This can be configured to suit
your needs.

Running `docker-compose up` from that directory will start two containers, one
running `jupyterhub` and another running `traefik`. N.B. Two docker volumes
will be created, as well as two docker networks.

Users logging into this example jupyterhub environment will have
`jupyterhub/singleuser` notebook servers launched for them in separate docker
containers (using `JupyterHub.DockerSpawner`). See
https://jupyterhub-dockerspawner.readthedocs.io/en/latest/docker-image.html for
instructions on building custom user notebook images. User data will be
persisted to separate docker volumes created for each user.

## Running tests

There are some tests that use *etcdctl* command line client for etcd. Make sure
to set environment variable `ETCDCTL_API=3` before running the tests, so that
the v3 API to be used, e.g.:

```
$ export ETCDCTL_API=3
```

You can then run the all the test suite from the *traefik-proxy* directory with:

```
$ pytest -v ./tests
```

Or you can run a specific test file with:

```
$ pytest -v ./tests/<test-file-name>
```
