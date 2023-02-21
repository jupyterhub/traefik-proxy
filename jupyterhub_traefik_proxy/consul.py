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

from urllib.parse import urlparse
import base64
import string

import escapism
from traitlets import default, Any, Unicode

from .kv_proxy import TKvProxy


class TraefikConsulProxy(TKvProxy):
    """JupyterHub Proxy implementation using traefik and Consul"""

    # Consul doesn't accept keys containing // or starting with / so we have to escape them
    key_safe_chars = string.ascii_letters + string.digits + "!@#$%^&*();<>-.+?:"

    @default("provider_name")
    def _provider_name(self):
        return "consul"

    consul_client_ca_cert = Unicode(
        config=True,
        allow_none=True,
        default_value=None,
        help="""Consul client root certificates""",
    )

    consul_url = Unicode(
        "http://127.0.0.1:8500",
        config=True,
        help="URL for the consul endpoint.",
    )
    consul_username = Unicode(
        "",
        config=True,
        help="Usrname for accessing consul.",
    )
    consul_password = Unicode(
        "",
        config=True,
        help="Password or token for accessing consul.",
    )

    kv_url = Unicode("DEPRECATED", config=True).tag(
        deprecated_in="0.4",
        deprecated_for="consul_url",
    )
    kv_username = Unicode("DEPRECATED", config=True).tag(
        deprecated_in="0.4",
        deprecated_for="consul_username",
    )
    kv_password = Unicode("DEPRECATED", config=True).tag(
        deprecated_in="0.4",
        deprecated_for="consul_password",
    )

    consul = Any()

    @default("consul")
    def _default_client(self):
        try:
            import consul.aio
        except ImportError:
            raise ImportError("Please install python-consul2 package to use traefik-proxy with consul")
        consul_service = urlparse(self.consul_url)
        kwargs = {
            "host": consul_service.hostname,
            "port": consul_service.port,
            "cert": self.consul_client_ca_cert,
        }
        if self.consul_password:
            kwargs.update({"token": self.consul_password})
        return consul.aio.Consul(**kwargs)

    def _define_kv_specific_static_config(self):
        provider_config = {
            "consul": {
                "rootKey": self.kv_traefik_prefix,
                "endpoints": [urlparse(self.consul_url).netloc],
            }
        }

        # FIXME: Same with the tls info
        if self.consul_client_ca_cert:
            provider_config["consul"]["tls"] = {"ca": self.consul_client_ca_cert}

        self.static_config.update({"providers": provider_config})

    def _start_traefik(self):
        if self.consul_password:
            if self.consul_username:
                self.traefik_env.setdefault(
                    "CONSUL_HTTP_AUTH", f"{self.consul_username}:{self.consul_password}"
                )
            else:
                self.traefik_env.setdefault("CONSUL_HTTP_TOKEN", self.consul_password)
        super()._start_traefik()

    def _stop_traefik(self):
        super()._stop_traefik()

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
            results = await self.consul.txn.put(payload=payload)
            status = 1
            response = ""
        except Exception as e:
            status = 0
            response = str(e)
            self.log.exception(f"Error uploading payload to KV store!\n{response}")
        else:
            self.log.debug("Successfully uploaded payload to KV store")

        return status, response

    async def _kv_atomic_add_route_parts(
        self, jupyterhub_routespec, target, data, route_keys, rule
    ):
        jupyterhub_target = self.kv_separator.join(
            [self.kv_jupyterhub_prefix, "targets", escapism.escape(target)]
        )

        payload = []
        def append_payload(key, value):
            payload.append({
                "KV": {
                    "Verb": "set",
                    "Key": key,
                    "Value": base64.b64encode(value.encode()).decode()
                }
            })
        append_payload(jupyterhub_routespec, target)
        append_payload(jupyterhub_target, data)
        append_payload(route_keys.service_url_path, target)
        append_payload(route_keys.router_service_path, route_keys.service_alias)
        append_payload(route_keys.router_rule_path, rule)

        router_path = self.kv_separator.join(
            ["traefik", "http", "routers", route_keys.router_alias]
        )
        if self.is_https:
            tls_path = self.kv_separator.join([router_path, "tls"])
            append_payload(tls_path, "true")
            if self.traefik_cert_resolver:
                tls_path = self.kv_separator.join([tls_path, "certResolver"])
                append_payload(tls_path, self.traefik_cert_resolver)

        # Specify the router's entryPoint
        if not self.traefik_entrypoint:
            self.traefik_entrypoint = await self._get_traefik_entrypoint()
        entrypoint_path = self.kv_separator.join([router_path, "entryPoints", "0"])
        append_payload(entrypoint_path, self.traefik_entrypoint)

        self.log.debug("Uploading route to KV store. Payload: %r", payload)
        try:
            results = await self.consul.txn.put(payload=payload)
            status = 1
            response = ""
        except Exception as e:
            status = 0
            response = str(e)

        return status, response

    async def _kv_atomic_delete_route_parts(self, jupyterhub_routespec, route_keys):

        index, v = await self.consul.kv.get(jupyterhub_routespec)
        if v is None:
            self.log.warning(
                "Route %s doesn't exist. Nothing to delete", jupyterhub_routespec
            )
            return True, None
        target = v["Value"]
        jupyterhub_target = self.kv_separator.join(
            [self.kv_jupyterhub_prefix, "targets", escapism.escape(target)]
        )

        payload=[
            {"KV": {"Verb": "delete", "Key": jupyterhub_routespec}},
            {"KV": {"Verb": "delete", "Key": jupyterhub_target}},
            {"KV": {"Verb": "delete", "Key": route_keys.service_url_path}},
            {"KV": {"Verb": "delete", "Key": route_keys.router_service_path}},
            {"KV": {"Verb": "delete", "Key": route_keys.router_rule_path}},
        ]

        if self.is_https:
            tls_path = self.kv_separator.join(
                ["traefik", "http", "routers", route_keys.router_alias, "tls"]
            )
            payload.append({"KV": {"Verb": "delete-tree", "Key": tls_path}})

        # delete any configured entrypoints
        payload.append({"KV": {"Verb": "delete-tree", "Key":
            self.kv_separator.join(
                ["traefik", "http", "routers", route_keys.router_alias, "entryPoints"]
            )
        }})

        try:
            status, response = await self.consul.txn.put(payload=payload)
            status = 1
            response = ""
        except Exception as e:
            status = 0
            response = str(e)

        return status, response

    async def _kv_get_target(self, jupyterhub_routespec):
        _, res = await self.consul.kv.get(jupyterhub_routespec)
        if res is None:
            return None
        return res["Value"].decode()

    async def _kv_get_data(self, target):
        _, res = await self.consul.kv.get(target)

        if res is None:
            return None
        return res["Value"].decode()

    async def _kv_get_route_parts(self, kv_entry):
        key = escapism.unescape(kv_entry["KV"]["Key"])
        value = kv_entry["KV"]["Value"]

        # Strip the "jupyterhub/routes/" prefix from the routespec
        sep = self.kv_separator
        route_prefix = sep.join(
            [self.kv_jupyterhub_prefix, "routes"]
        )
        routespec = key.replace(route_prefix + sep, "")

        target = base64.b64decode(value.encode()).decode()
        jupyterhub_target = sep.join(
            [self.kv_jupyterhub_prefix, "targets", escapism.escape(target)]
        )

        data = await self._kv_get_data(jupyterhub_target)

        return routespec, target, data

    async def _kv_get_jupyterhub_prefixed_entries(self):
        routes = await self.consul.txn.put(
            payload=[
                {
                    "KV": {
                        "Verb": "get-tree",
                        "Key": self.kv_separator.join(
                            [self.kv_jupyterhub_prefix, "routes"]
                        )
                    }
                }
            ]
        )

        return routes["Results"]

    async def stop(self):
        await super().stop()
