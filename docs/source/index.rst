.. JupyterHub Traefik Proxy documentation master file, created by
   sphinx-quickstart on Tue Nov 20 11:54:09 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

========================
JupyterHub Traefik Proxy
========================

An implementation of the JupyterHub proxy api with `traefik <https://traefik.io>`__ : an extremely lightweight, portable reverse proxy implementation, that supports load balancing and can configure itself automatically and dynamically. 

Why traefik?
============

Currently, the **default** proxy implementation for JupyterHub is `configurable-http-proxy <https://github.com/jupyterhub/configurable-http-proxy>`__ (CHP), which stores the routing table in-memory. This might be the best approach in most of the cases, but because you can only run a single copy of the proxy at a time, it has its limitations when used in dynamic large scale systems.

When using a proxy implementation based on traefik, you can run multiple instances of traefik by using a distributed key-value store like `etcd <https://coreos.com/etcd>`__ or `consul <https://www.consul.io/>`__ to store the routing table. This makes the proxy **highly available** and improves the scalability and stability of the system.
Moreover it offers *HTTPS* support through a straight-forward `ACME (Let's Encrypt) <https://docs.traefik.io/configuration/acme>`__ configuration.

There are three versions for the proxy, depending on how traefik stores the routes:

* *for* **smaller**, *single-node deployments*:
   * TraefikFileProviderProxy
* *for* **distributed** *setups*:
   * TraefikEtcdProxy
   * TraefikConsulProxy

Contents
========
Installation Guide
------------------
.. toctree::
   :maxdepth: 2

   install
   docker-compose

Getting Started
---------------
.. toctree::
   :maxdepth: 1

   file
   etcd
   consul

API Reference
-------------
.. toctree::
   :maxdepth: 3

   api/index
   changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
