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
from urllib.parse import urlparse

import escapism
from tornado.concurrent import run_on_executor
from traitlets import Any, Bool, List, Unicode, default

from .kv_proxy import TKvProxy


class TraefikEtcdProxy(TKvProxy):
    """JupyterHub Proxy implementation using traefik and etcd"""

    executor = Any()

    @default("provider_name")
    def _provider_name(self):
        return "etcd"

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

    # The grpc client (used by the Python etcd library) doesn't allow untrusted
    # etcd certificates, although traefik does allow them.
    etcd_insecure_skip_verify = Bool(
        False,
        config=True,
        help="""Traefik will by default validate SSL certificate of etcd backend""",
    )

    grpc_options = List(
        config=True,
        allow_none=True,
        default_value=None,
        help="""Any grpc options that need to be passed to the etcd client""",
    )

    @default("executor")
    def _default_executor(self):
        return ThreadPoolExecutor(1)

    etcd_url = Unicode(
        "http://127.0.0.1:2379",
        config=True,
        help="URL for the etcd endpoint.",
    )

    etcd_username = Unicode(
        "",
        config=True,
        help="Username for accessing etcd.",
    )
    etcd_password = Unicode(
        "",
        config=True,
        help="Password for accessing etcd.",
    )

    kv_url = Unicode("DEPRECATED", config=True).tag(
        deprecated_in="0.4",
        deprecated_for="etcd_url",
    )
    kv_username = Unicode("DEPRECATED", config=True).tag(
        deprecated_in="0.4",
        deprecated_for="etcd_username",
    )
    kv_password = Unicode("DEPRECATED", config=True).tag(
        deprecated_in="0.4",
        deprecated_for="etcd_password",
    )

    etcd = Any()

    @default("etcd")
    def _default_client(self):
        etcd_service = urlparse(self.etcd_url)
        try:
            import etcd3
        except ImportError:
            raise ImportError(
                "Please install etcd3 or etcdpy package to use traefik-proxy with etcd3"
            )
        kwargs = {
            'host': etcd_service.hostname,
            'port': etcd_service.port,
            'ca_cert': self.etcd_client_ca_cert,
            'cert_cert': self.etcd_client_cert_crt,
            'cert_key': self.etcd_client_cert_key,
            'grpc_options': self.grpc_options,
        }
        if self.etcd_password:
            kwargs.update(
                {
                    "user": self.etcd_username,
                    "password": self.etcd_password,
                }
            )
        return etcd3.client(**kwargs)

    def _cleanup(self):
        super()._cleanup()
        self.etcd.close()

    @run_on_executor
    def _etcd_transaction(self, success_actions):
        status, response = self.etcd.transaction(
            compare=[], success=success_actions, failure=[]
        )
        return status, response

    @run_on_executor
    def _etcd_get(self, key):
        value, _ = self.etcd.get(key)
        return value

    @run_on_executor
    def _etcd_get_prefix(self, prefix):
        routes = self.etcd.get_prefix(prefix)
        return routes

    def _define_kv_specific_static_config(self):
        self.log.debug("Setting up the etcd provider in the static config")
        url = urlparse(self.etcd_url)
        self.static_config.update(
            {
                "providers": {
                    "etcd": {
                        "endpoints": [url.netloc],
                        "rootKey": self.kv_traefik_prefix,
                    }
                }
            }
        )
        if url.scheme == "https":
            # If etcd is running over TLS, then traefik needs to know
            tls_conf = {}
            if self.etcd_client_ca_cert is not None:
                tls_conf["ca"] = self.etcd_client_ca_cert
            tls_conf["insecureSkipVerify"] = self.etcd_insecure_skip_verify
            self.static_config["providers"]["etcd"]["tls"] = tls_conf

        if self.etcd_username and self.etcd_password:
            self.static_config["providers"]["etcd"].update(
                {
                    "username": self.etcd_username,
                    "password": self.etcd_password,
                }
            )

    async def _kv_atomic_add_route_parts(
        self, jupyterhub_routespec, target, data, route_keys, rule
    ):
        # e.g. jupyterhub_target = 'jupyter/targets/{http://foobar.com}'
        # where {http://foobar.com} is escaped
        jupyterhub_target = self.kv_separator.join(
            [self.kv_jupyterhub_prefix, "targets", escapism.escape(target)]
        )
        put = self.etcd.transactions.put
        success = [
            # e.g. jupyter/routers/router-1 = {target}
            put(jupyterhub_routespec, target),
            # e.g. jupyter/targets/{escaped_target} = {data}
            put(jupyterhub_target, data),
            # e.g. http/services/service-1/loadBalancer/servers/server1 = target
            put(route_keys.service_url_path, target),
            # e.g. http/routers/router-1/service = service-1
            put(route_keys.router_service_path, route_keys.service_alias),
            # e.g. http/routers/router-1/rule = {rule}
            put(route_keys.router_rule_path, rule),
        ]
        # Optionally enable TLS on this router
        router_key = self.kv_separator.join(
            ["traefik", "http", "routers", route_keys.router_alias]
        )
        if self.is_https:
            tls_path = self.kv_separator.join([router_key, "tls"])
            tls_value = ""
            if self.traefik_cert_resolver:
                tls_path = self.kv_separator.join([tls_path, "certResolver"])
                tls_value = self.traefik_cert_resolver
            success.append(put(tls_path, tls_value))

        # Specify the entrypoint that jupyterhub's router should bind to
        ep_path = self.kv_separator.join([router_key, "entryPoints", "0"])
        if not self.traefik_entrypoint:
            self.traefik_entrypoint = await self._get_traefik_entrypoint()
        success.append(put(ep_path, self.traefik_entrypoint))

        status, response = await self._etcd_transaction(success)
        return status, response

    async def _kv_atomic_delete_route_parts(self, jupyterhub_routespec, route_keys):
        value = await self._etcd_get(jupyterhub_routespec)
        if value is None:
            self.log.warning(
                f"Route {jupyterhub_routespec} doesn't exist. Nothing to delete"
            )
            return True, None

        jupyterhub_target = self.kv_separator.join(
            [self.kv_jupyterhub_prefix, "targets", escapism.escape(value.decode())]
        )

        router_path = self.kv_separator.join(
            ["traefik", "http", "routers", route_keys.router_alias]
        )
        delete = self.etcd.transactions.delete
        success = [
            delete(jupyterhub_routespec),
            delete(jupyterhub_target),
            delete(route_keys.service_url_path),
            delete(route_keys.router_service_path),
            delete(route_keys.router_rule_path),
            delete(self.kv_separator.join([router_path, "entryPoints", "0"])),
        ]
        # If it was enabled, delete TLS on the router too
        if self.is_https:
            tls_path = self.kv_separator.join([router_path, "tls"])
            if self.traefik_cert_resolver:
                tls_path = self.kv_separator.join([tls_path, "certResolver"])
            success.append(delete(tls_path))

        status, response = await self._etcd_transaction(success)
        return status, response

    async def _kv_get_target(self, jupyterhub_routespec):
        value = await self._etcd_get(jupyterhub_routespec)
        if value is None:
            return None
        return value.decode()

    async def _kv_get_data(self, target):
        value = await self._etcd_get(target)
        if value is None:
            return None
        return value

    async def _kv_get_route_parts(self, kv_entry):
        key = kv_entry[1].key.decode()
        value = kv_entry[0].decode()

        # Strip the "/jupyterhub/routes/" prefix from the routespec and unescape it
        sep = self.kv_separator
        route_prefix = sep.join([self.kv_jupyterhub_prefix, "routes" + sep])
        target_prefix = sep.join([self.kv_jupyterhub_prefix, "targets"])
        routespec = escapism.unescape(key.replace(route_prefix, "", 1))
        etcd_target = sep.join([target_prefix, escapism.escape(value)])
        target = escapism.unescape(etcd_target.replace(target_prefix + sep, "", 1))
        data = await self._kv_get_data(etcd_target)

        return routespec, target, data

    async def _kv_get_jupyterhub_prefixed_entries(self):
        sep = self.kv_separator
        routespecs_prefix = sep.join([self.kv_jupyterhub_prefix, "routes" + sep])
        routes = await self._etcd_get_prefix(routespecs_prefix)
        return routes

    async def persist_dynamic_config(self):
        data = self.flatten_dict_for_kv(
            self.dynamic_config, prefix=self.kv_traefik_prefix
        )
        transactions = []
        for k, v in data.items():
            transactions.append(self.etcd.transactions.put(k, v))
        status, response = await self._etcd_transaction(transactions)
        return status, response
