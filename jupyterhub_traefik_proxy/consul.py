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

import json
import os
from urllib.parse import urlparse
import string
import base64

import asyncio
import consul.aio
import escapism
from tornado.concurrent import run_on_executor
from traitlets import Any, default, Unicode

from . import traefik_utils
from jupyterhub_traefik_proxy import TKvProxy
import time


class TraefikConsulProxy(TKvProxy):
    """JupyterHub Proxy implementation using traefik and Consul"""

    # Consul doesn't accept keys containing // or starting with / so we have to escape them
    key_safe_chars = string.ascii_letters + string.digits + "!@#$%^&*();<>_-.+?:"

    kv_name = "consul"

    consul_client_ca_cert = Unicode(
        config=True,
        allow_none=True,
        default_value=None,
        help="""Consul client root certificates""",
    )

    @default("kv_url")
    def _default_kv_url(self):
        return "http://127.0.0.1:8500"

    @default("kv_client")
    def _default_client(self):
        consul_service = urlparse(self.kv_url)
        if self.kv_password:
            client = consul.aio.Consul(
                host=str(consul_service.hostname),
                port=consul_service.port,
                token=self.kv_password,
                cert=self.consul_client_ca_cert,
            )
            client.http._session._default_headers.update(
                {"X-Consul-Token": self.kv_password}
            )
            return client
        return consul.aio.Consul(
            host=str(consul_service.hostname),
            port=consul_service.port,
            cert=self.consul_client_ca_cert,
        )

    @default("kv_traefik_prefix")
    def _default_kv_traefik_prefix(self):
        return "traefik/"

    @default("kv_jupyterhub_prefix")
    def _default_kv_jupyterhub_prefix(self):
        return "jupyterhub/"

    def _define_kv_specific_static_config(self):
        self.static_config["consul"] = {
            "endpoint": str(urlparse(self.kv_url).hostname)
            + ":"
            + str(urlparse(self.kv_url).port),
            "prefix": self.kv_traefik_prefix,
            "watch": True,
        }

    def _launch_traefik(self, config_type):
        os.environ["CONSUL_HTTP_TOKEN"] = self.kv_password
        super()._launch_traefik(config_type)

    async def _kv_atomic_add_route_parts(
        self, jupyterhub_routespec, target, data, route_keys, rule
    ):
        escaped_target = escapism.escape(target, safe=self.key_safe_chars)
        escaped_jupyterhub_routespec = escapism.escape(
            jupyterhub_routespec, safe=self.key_safe_chars
        )

        try:
            results = await self.kv_client.txn.put(
                payload=[
                    {
                        "KV": {
                            "Verb": "set",
                            "Key": escaped_jupyterhub_routespec,
                            "Value": base64.b64encode(target.encode()).decode(),
                        }
                    },
                    {
                        "KV": {
                            "Verb": "set",
                            "Key": escaped_target,
                            "Value": base64.b64encode(data.encode()).decode(),
                        }
                    },
                    {
                        "KV": {
                            "Verb": "set",
                            "Key": route_keys.backend_url_path,
                            "Value": base64.b64encode(target.encode()).decode(),
                        }
                    },
                    {
                        "KV": {
                            "Verb": "set",
                            "Key": route_keys.backend_weight_path,
                            "Value": base64.b64encode(b"1").decode(),
                        }
                    },
                    {
                        "KV": {
                            "Verb": "set",
                            "Key": route_keys.frontend_backend_path,
                            "Value": base64.b64encode(
                                route_keys.backend_alias.encode()
                            ).decode(),
                        }
                    },
                    {
                        "KV": {
                            "Verb": "set",
                            "Key": route_keys.frontend_rule_path,
                            "Value": base64.b64encode(rule.encode()).decode(),
                        }
                    },
                ]
            )
            status = 1
            response = ""
        except Exception as e:
            status = 0
            response = str(e)

        return status, response

    async def _kv_atomic_delete_route_parts(self, jupyterhub_routespec, route_keys):
        escaped_jupyterhub_routespec = escapism.escape(
            jupyterhub_routespec, safe=self.key_safe_chars
        )

        index, v = await self.kv_client.kv.get(escaped_jupyterhub_routespec)
        if v is None:
            self.log.warning("Route %s doesn't exist. Nothing to delete", routespec)
            return
        target = v["Value"]
        escaped_target = escapism.escape(target, safe=self.key_safe_chars)

        try:
            status, response = await self.kv_client.txn.put(
                payload=[
                    {"KV": {"Verb": "delete", "Key": escaped_jupyterhub_routespec}},
                    {"KV": {"Verb": "delete", "Key": escaped_target}},
                    {"KV": {"Verb": "delete", "Key": route_keys.backend_url_path}},
                    {"KV": {"Verb": "delete", "Key": route_keys.backend_weight_path}},
                    {"KV": {"Verb": "delete", "Key": route_keys.frontend_backend_path}},
                    {"KV": {"Verb": "delete", "Key": route_keys.frontend_rule_path}},
                ]
            )
            status = 1
            response = ""
        except Exception as e:
            status = 0
            response = str(e)

        return status, response

    async def _kv_get_target(self, jupyterhub_routespec):
        escaped_jupyterhub_routespec = escapism.escape(
            jupyterhub_routespec, safe=self.key_safe_chars
        )
        _, res = await self.kv_client.kv.get(escaped_jupyterhub_routespec)
        if res is None:
            return None
        return res["Value"].decode()

    async def _kv_get_data(self, target):
        escaped_target = escapism.escape(target, safe=self.key_safe_chars)
        _, res = await self.kv_client.kv.get(escaped_target)

        if res is None:
            return None
        return res["Value"].decode()

    async def _kv_get_route_parts(self, kv_entry):
        key = escapism.unescape(kv_entry["KV"]["Key"])
        value = kv_entry["KV"]["Value"]

        # Strip the "/jupyterhub" prefix from the routespec
        routespec = key.replace(self.kv_jupyterhub_prefix, "")
        target = base64.b64decode(value.encode()).decode()
        data = await self._kv_get_data(target)

        return routespec, target, data

    async def _kv_get_jupyterhub_prefixed_entries(self):
        routes = await self.kv_client.txn.put(
            payload=[
                {
                    "KV": {
                        "Verb": "get-tree",
                        "Key": escapism.escape(
                            self.kv_jupyterhub_prefix, safe=self.key_safe_chars
                        ),
                    }
                }
            ]
        )

        return routes["Results"]

    async def stop(self):
        await super().stop()
        await self.kv_client.http._session.close()
