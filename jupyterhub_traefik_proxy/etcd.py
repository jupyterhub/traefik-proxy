"""Traefik implementation

Custom proxy implementations can subclass :class:`Proxy`
and register in JupyterHub config:

.. sourcecode:: python

    from mymodule import MyProxy
    c.JupyterHub.proxy_class = MyProxy

Route Specification:

- A routespec is a URL prefix ([host]/path/), e.g.
  'host.tld/path/' for host-based routing or '/path/' for default routing.
- Route paths should be normalized to always start and end with '/'
"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from concurrent.futures import ThreadPoolExecutor
import json
import os
from urllib.parse import urlparse

import etcd3
from tornado.concurrent import run_on_executor
from traitlets import Any, default, Unicode

from jupyterhub.utils import maybe_future
from . import traefik_utils
from jupyterhub_traefik_proxy import TKvProxy


class TraefikEtcdProxy(TKvProxy):
    """JupyterHub Proxy implementation using traefik and etcd"""

    executor = Any()

    kv_name = "etcdv3"

    etcd_client_ca_cert = Unicode(
        config=True,
        allow_none=True,
        default_value=None,
        help="""Etcd client root certificates""",
    )

    etcd_client_cert_crt = Unicode(
        config=True,
        allow_none=True,
        default_value=None,
        help="""Etcd client certificate chain
            (etcd_client_cert_key must also be specified)""",
    )

    etcd_client_cert_key = Unicode(
        config=True,
        allow_none=True,
        default_value=None,
        help="""Etcd client private key
            (etcd_client_cert_crt must also be specified)""",
    )

    @default("executor")
    def _default_executor(self):
        return ThreadPoolExecutor(1)

    @default("kv_url")
    def _default_kv_url(self):
        return "http://127.0.0.1:2379"

    @default("kv_client")
    def _default_client(self):
        etcd_service = urlparse(self.kv_url)
        if self.kv_password:
            return etcd3.client(
                host=str(etcd_service.hostname),
                port=etcd_service.port,
                user=self.kv_username,
                password=self.kv_password,
                ca_cert=self.etcd_client_ca_cert,
                cert_cert=self.etcd_client_cert_crt,
                cert_key=self.etcd_client_cert_key,
            )
        return etcd3.client(
            host=str(etcd_service.hostname),
            port=etcd_service.port,
            ca_cert=self.etcd_client_ca_cert,
            cert_cert=self.etcd_client_cert_crt,
            cert_key=self.etcd_client_cert_key,
        )

    @default("kv_traefik_prefix")
    def _default_kv_traefik_prefix(self):
        return "/traefik/"

    @default("kv_jupyterhub_prefix")
    def _default_kv_jupyterhub_prefix(self):
        return "/jupyterhub/"

    @run_on_executor
    def _etcd_transaction(self, success_actions):
        status, response = self.kv_client.transaction(
            compare=[], success=success_actions, failure=[]
        )
        return status, response

    @run_on_executor
    def _etcd_get(self, key):
        value, _ = self.kv_client.get(key)
        return value

    @run_on_executor
    def _etcd_get_prefix(self, prefix):
        routes = self.kv_client.get_prefix(prefix)
        return routes

    def _define_kv_specific_static_config(self):
        self.static_config["etcd"] = {
            "username": self.kv_username,
            "password": self.kv_password,
            "endpoint": str(urlparse(self.kv_url).hostname)
            + ":"
            + str(urlparse(self.kv_url).port),
            "prefix": self.kv_traefik_prefix,
            "useapiv3": True,
            "watch": True,
        }

    async def _kv_atomic_add_route_parts(
        self, jupyterhub_routespec, target, data, route_keys, rule
    ):
        success = [
            self.kv_client.transactions.put(jupyterhub_routespec, target),
            self.kv_client.transactions.put(target, data),
            self.kv_client.transactions.put(route_keys.backend_url_path, target),
            self.kv_client.transactions.put(route_keys.backend_weight_path, "1"),
            self.kv_client.transactions.put(
                route_keys.frontend_backend_path, route_keys.backend_alias
            ),
            self.kv_client.transactions.put(route_keys.frontend_rule_path, rule),
        ]
        status, response = await maybe_future(self._etcd_transaction(success))
        return status, response

    async def _kv_atomic_delete_route_parts(self, jupyterhub_routespec, route_keys):
        value = await maybe_future(self._etcd_get(jupyterhub_routespec))
        if value is None:
            self.log.warning("Route %s doesn't exist. Nothing to delete", routespec)
            return

        target = value.decode()

        success = [
            self.kv_client.transactions.delete(jupyterhub_routespec),
            self.kv_client.transactions.delete(target),
            self.kv_client.transactions.delete(route_keys.backend_url_path),
            self.kv_client.transactions.delete(route_keys.backend_weight_path),
            self.kv_client.transactions.delete(route_keys.frontend_backend_path),
            self.kv_client.transactions.delete(route_keys.frontend_rule_path),
        ]
        status, response = await maybe_future(self._etcd_transaction(success))
        return status, response

    async def _kv_get_target(self, jupyterhub_routespec):
        value = await maybe_future(self._etcd_get(jupyterhub_routespec))
        if value == None:
            return None
        return value.decode()

    async def _kv_get_data(self, target):
        value = await maybe_future(self._etcd_get(target))
        if value is None:
            return None
        return value

    async def _kv_get_route_parts(self, kv_entry):
        key = kv_entry[1].key.decode()
        value = kv_entry[0]

        # Strip the "/jupyterhub" prefix from the routespec
        routespec = key.replace(self.kv_jupyterhub_prefix, "")
        target = value.decode()
        data = await self._kv_get_data(target)

        return routespec, target, data

    async def _kv_get_jupyterhub_prefixed_entries(self):
        routes = await maybe_future(self._etcd_get_prefix(self.kv_jupyterhub_prefix))
        return routes
