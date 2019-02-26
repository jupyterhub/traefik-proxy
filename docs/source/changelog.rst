.. _changelog:

Changes in jupyterhub-traefik-proxy
===================================

Unreleased
----------

0.1.3
-----

- Load initial routing table from disk in TraefikTomlProxy
  when resuming from a previous session.

0.1.2
-----

- Fix possible race in atomic_writing with TraefikTomlProxy

0.1.1
-----

- make proxytest reusable with any Proxy implementation
- improve documentation
- improve logging and error handling
- make check_route_timeout configurable

0.1.0
-----

First release!
