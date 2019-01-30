.. JupyterHub Traefik Proxy documentation master file, created by
   sphinx-quickstart on Tue Nov 20 11:54:09 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

JupyterHub Traefik Proxy
========================

An implementation of the JupyterHub proxy api with `traefik <https://traefik.io>`__.

Installation
============

There are two versions for the proxy, dependig on how traefik stores the routes:

* TraefikTomlProxy
* TraefikEtcdProxy

Version: |version|

TODO:

- what is traefik
- why use traefik instead of the default configurable-http-proxy (supports letsencrypt, works with etcd, can have multiple copies for scaling/stability)?
- when to use etcd or toml


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   install
   toml
   etcd

   api/index
   changelog



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
