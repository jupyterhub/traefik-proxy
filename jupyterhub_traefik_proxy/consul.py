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
import escapism
from tornado.concurrent import run_on_executor
from traitlets import Any, default, Unicode

from . import traefik_utils
from jupyterhub_traefik_proxy import TKvProxy
import time


class TraefikConsulProxy(TKvProxy):
    """JupyterHub Proxy implementation using traefik and Consul"""

    # Consul doesn't accept keys containing // or starting with / so we have to escape them
    key_safe_chars = string.ascii_letters + string.digits + "!@#$%^&*();<>-.+?:"

    #kv_name = "consul"

    @default("provider_name")
    def _provider_name(self):
        return "consul"

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
        try:
            import consul.aio
        except ImportError:
            raise ImportError("Please install python-consul2 package to use traefik-proxy with consul")
        consul_service = urlparse(self.kv_url)
        kwargs = {
            'host': consul_service.hostname,
            'port': consul_service.port,
            'cert': self.consul_client_ca_cert
        }
        if self.kv_password:
            kwargs.update({'token': self.kv_password})
        return consul.aio.Consul(**kwargs)

    def _define_kv_specific_static_config(self):
        provider_config = {
            "consul": {
                "rootKey": self.kv_traefik_prefix,
                #"watch": True,
                "endpoints" : [
                    urlparse(self.kv_url).netloc
                ]
            }
        }
        # Q: Why weren't these in the Traefik v1 implementation?
        # A: Although defined in the traefik docs, they appear to
        # do nothing, and CONSUL_HTTP_TOKEN needs to be used instead.
        # Ref: https://github.com/traefik/traefik/issues/767#issuecomment-270096663
        if self.kv_username:
            provider_config["consul"].update({"username": self.kv_username})

        if self.kv_password:
            provider_config["consul"].update({"password": self.kv_password})

        # FIXME: Same with the tls info
        if self.consul_client_ca_cert:
            provider_config["consul"]["tls"] = {
                "ca" : self.consul_client_ca_cert
            }

        self.static_config.update({"providers": provider_config})
            
    def _start_traefik(self):
        os.environ["CONSUL_HTTP_TOKEN"] = self.kv_password
        super()._start_traefik()

    def _stop_traefik(self):
        super()._stop_traefik()
        if "CONSUL_HTTP_TOKEN" in os.environ:
            os.environ.pop("CONSUL_HTTP_TOKEN")

    async def persist_dynamic_config(self):
        data = self.flatten_dict_for_kv(
            self.dynamic_config, prefix=self.kv_traefik_prefix
        )
        payload = []
        def append_payload(key, val):
            payload.append({
                "KV": {
                    "Verb": "set",
                    "Key": key,
                    "Value": base64.b64encode(val.encode()).decode(),
                }
            })
        for k,v in data.items():
            append_payload(k, v)

        try:
            results = await self.kv_client.txn.put(payload=payload)
            status = 1
            response = ""
        except Exception as e:
            status = 0
            response = str(e)
            self.log.exception(f"Error uploading payload to KV store!\n{response}")
            self.log.exception(f"Are you missing a token? {self.kv_client.token}")
        else:
            self.log.debug("Successfully uploaded payload to KV store")

        return status, response

    async def _kv_atomic_add_route_parts(
        self, jupyterhub_routespec, target, data, route_keys, rule
    ):
        jupyterhub_target = self.kv_separator.join(
            [self.kv_jupyterhub_prefix, "targets", escapism.escape(target)]
        )

        try:
            payload=[
                {
                    "KV": {
                        "Verb": "set",
                        "Key": jupyterhub_routespec,
                        "Value": base64.b64encode(target.encode()).decode(),
                    }
                },
                {
                    "KV": {
                        "Verb": "set",
                        "Key": jupyterhub_target,
                        "Value": base64.b64encode(data.encode()).decode(),
                    }
                },
                {
                    "KV": {
                        "Verb": "set",
                        "Key": route_keys.service_url_path,
                        "Value": base64.b64encode(target.encode()).decode(),
                    }
                },
                {
                    "KV": {
                        "Verb": "set",
                        "Key": route_keys.router_service_path,
                        "Value": base64.b64encode(
                            route_keys.service_alias.encode()
                        ).decode(),
                    }
                },
                {
                    "KV": {
                        "Verb": "set",
                        "Key": route_keys.router_rule_path,
                        "Value": base64.b64encode(rule.encode()).decode(),
                    }
                }
            ]
            self.log.debug(f"Uploading route to KV store. Payload: {repr(payload)}")
            results = await self.kv_client.txn.put(payload=payload)
            status = 1
            response = ""
        except Exception as e:
            status = 0
            response = str(e)

        return status, response

    async def _kv_atomic_delete_route_parts(self, jupyterhub_routespec, route_keys):

        index, v = await self.kv_client.kv.get(jupyterhub_routespec)
        if v is None:
            self.log.warning(
                "Route %s doesn't exist. Nothing to delete", jupyterhub_routespec
            )
            return True, None
        target = v["Value"]
        jupyterhub_target = self.kv_separator.join(
            [self.kv_jupyterhub_prefix, "targets", escapism.escape(target)]
        )

        try:
            status, response = await self.kv_client.txn.put(
                payload=[
                    {"KV": {"Verb": "delete", "Key": jupyterhub_routespec}},
                    {"KV": {"Verb": "delete", "Key": jupyterhub_target}},
                    {"KV": {"Verb": "delete", "Key": route_keys.service_url_path}},
                    {"KV": {"Verb": "delete", "Key": route_keys.router_service_path}},
                    {"KV": {"Verb": "delete", "Key": route_keys.router_rule_path}},
                ]
            )
            status = 1
            response = ""
        except Exception as e:
            status = 0
            response = str(e)

        return status, response

    async def _kv_get_target(self, jupyterhub_routespec):
        _, res = await self.kv_client.kv.get(jupyterhub_routespec)
        if res is None:
            return None
        return res["Value"].decode()

    async def _kv_get_data(self, target):
        _, res = await self.kv_client.kv.get(target)

        if res is None:
            return None
        return res["Value"].decode()

    async def _kv_get_route_parts(self, kv_entry):
        key = escapism.unescape(kv_entry["KV"]["Key"])
        value = kv_entry["KV"]["Value"]

        # Strip the "jupyterhub/routes/" prefix from the routespec
        route_prefix = self.kv_separator.join(
            [self.kv_jupyterhub_prefix, "routes/"]
        )
        routespec = key.replace(route_prefix, "")

        target = base64.b64decode(value.encode()).decode()
        jupyterhub_target = self.kv_separator.join(
            [self.kv_jupyterhub_prefix, "targets", escapism.escape(target)]
        )

        data = await self._kv_get_data(jupyterhub_target)

        return routespec, target, data

    async def _kv_get_jupyterhub_prefixed_entries(self):
        routes = await self.kv_client.txn.put(
            payload=[
                {
                    "KV": {
                        "Verb": "get-tree",
                        "Key": f"{self.kv_jupyterhub_prefix}/routes"
                        #escapism.escape(
                        #    self.kv_jupyterhub_prefix, safe=self.key_safe_chars
                        #)+ "/routes",
                    }
                }
            ]
        )

        return routes["Results"]

    async def stop(self):
        await super().stop()

