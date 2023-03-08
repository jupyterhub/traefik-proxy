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

import asyncio
import os

import escapism
from traitlets import Any, Unicode, default, observe

from . import traefik_utils
from .proxy import TraefikProxy


class TraefikFileProviderProxy(TraefikProxy):
    """JupyterHub Proxy implementation using traefik and toml or yaml config file"""

    mutex = Any()

    @default("mutex")
    def _default_mutex(self):
        return asyncio.Lock()

    @default("provider_name")
    def _provider_name(self):
        return "file"

    dynamic_config_file = Unicode(
        "rules.toml", config=True, help="""traefik's dynamic configuration file"""
    )

    dynamic_config_handler = Any()

    @default("dynamic_config_handler")
    def _default_handler(self):
        return traefik_utils.TraefikConfigFileHandler(self.dynamic_config_file)

    # If dynamic_config_file is changed, then update the dynamic config file handler
    @observe("dynamic_config_file")
    def _set_dynamic_config_file(self, change):
        self.dynamic_config_handler = traefik_utils.TraefikConfigFileHandler(
            self.dynamic_config_file
        )

    @default("dynamic_config")
    def _load_dynamic_config(self):
        try:
            # Load initial dynamic config from disk
            dynamic_config = self.dynamic_config_handler.load()
        except FileNotFoundError:
            dynamic_config = {}

        # fill in default keys
        # use setdefault to ensure these are always fully defined
        # and never _partially_ defined
        http = dynamic_config.setdefault("http", {})
        http.setdefault("services", {})
        http.setdefault("routers", {})
        jupyter = dynamic_config.setdefault("jupyter", {})
        jupyter.setdefault("routers", {})
        return dynamic_config

    def persist_dynamic_config(self):
        """Save the dynamic config file with the current dynamic_config"""
        # avoid writing empty dicts, which traefik doesn't handle for some reason
        dynamic_config = self.dynamic_config
        if (
            not dynamic_config["http"]["routers"]
            or not dynamic_config["http"]["services"]
        ):
            # traefik can't handle empty dicts, so don't persist them.
            # But don't _remove_ them from our own config
            # I think this is a bug in traefik - empty dicts satisfy the spec
            # use shallow copy, which is cheap but most be done at every level where we modify keys
            dynamic_config = dynamic_config.copy()
            dynamic_config["http"] = http = dynamic_config["http"].copy()
            for key in ("routers", "services"):
                if not http[key]:
                    http.pop(key)
            if not http:
                dynamic_config.pop("http")
        self.dynamic_config_handler.atomic_dump(dynamic_config)

    async def _setup_traefik_dynamic_config(self):
        await super()._setup_traefik_dynamic_config()
        self.log.info(
            f"Creating the dynamic configuration file: {self.dynamic_config_file}"
        )
        self.persist_dynamic_config()

    async def _setup_traefik_static_config(self):
        self.static_config["providers"] = {
            "file": {"filename": self.dynamic_config_file, "watch": True}
        }
        await super()._setup_traefik_static_config()

    def _clean_resources(self):
        try:
            if self.should_start:
                os.remove(self.static_config_file)
            os.remove(self.dynamic_config_file)
        except:
            self.log.error("Failed to remove traefik's configuration files")
            raise

    def _get_route_unsafe(self, traefik_routespec):
        service_alias = traefik_utils.generate_alias(traefik_routespec, "service")
        router_alias = traefik_utils.generate_alias(traefik_routespec, "router")
        routespec = self.validate_routespec(traefik_routespec)
        result = {"data": None, "target": None, "routespec": routespec}

        service_node = self.dynamic_config["http"]["services"].get(service_alias, None)
        if service_node is not None:
            # Will this ever cause a KeyError?
            result["target"] = service_node["loadBalancer"]["servers"][0]["url"]

        jupyter_routers = self.dynamic_config["jupyter"]["routers"].get(
            router_alias, None
        )
        if jupyter_routers is not None:
            result["data"] = jupyter_routers["data"]

        if result["data"] is None and result["target"] is None:
            self.log.info(f"No route for {routespec} found!")
            result = None
        return result

    async def start(self):
        """Start the proxy.

        Will be called during startup if should_start is True.

        **Subclasses must define this method**
        if the proxy is to be started by the Hub
        """
        await super().start()
        await self._wait_for_static_config()

    async def stop(self):
        """Stop the proxy.

        Will be called during teardown if should_start is True.

        **Subclasses must define this method**
        if the proxy is to be started by the Hub
        """
        await super().stop()
        self._clean_resources()

    async def add_route(self, routespec, target, data):
        """Add a route to the proxy.

        **Subclasses must define this method**

        Args:
            routespec (str): A URL prefix ([host]/path/) for which this route will be matched,
                e.g. host.name/path/
            target (str): A full URL that will be the target of this route.
            data (dict): A JSONable dict that will be associated with this route, and will
                be returned when retrieving information about this route.

        Will raise an appropriate Exception (FIXME: find what?) if the route could
        not be added.

        The proxy implementation should also have a way to associate the fact that a
        route came from JupyterHub.
        """
        traefik_routespec = self.validate_routespec(routespec)
        service_alias = traefik_utils.generate_alias(traefik_routespec, "service")
        router_alias = traefik_utils.generate_alias(traefik_routespec, "router")
        rule = traefik_utils.generate_rule(traefik_routespec)

        if not self.traefik_entrypoint:
            self.traefik_entrypoint = await self._get_traefik_entrypoint()

        async with self.mutex:
            self.dynamic_config["http"]["routers"][router_alias] = {
                "service": service_alias,
                "rule": rule,
                "entryPoints": [self.traefik_entrypoint],
            }

            # Enable TLS on this router if globally enabled
            if self.is_https:
                tls_config = {}
                if self.traefik_cert_resolver:
                    tls_config["certResolver"] = self.traefik_cert_resolver

                self.dynamic_config["http"]["routers"][router_alias].update(
                    {"tls": tls_config}
                )

            # Add the data node to a separate top-level node, so traefik doesn't complain.
            self.dynamic_config["jupyter"]["routers"][router_alias] = {"data": data}

            self.dynamic_config["http"]["services"][service_alias] = {
                "loadBalancer": {"servers": [{"url": target}], "passHostHeader": True}
            }
            self.persist_dynamic_config()

        if self.should_start:
            try:
                # Check if traefik was launched
                self.traefik_process.pid
            except AttributeError:
                self.log.error(
                    "You cannot add routes if the proxy isn't running! Please start the proxy: proxy.start()"
                )
                raise
        try:
            await self._wait_for_route(traefik_routespec)
        except TimeoutError:
            self.log.error(
                f"Is Traefik configured to watch {self.dynamic_config_file}?"
            )
            raise

    async def delete_route(self, routespec):
        """Delete a route with a given routespec if it exists.

        **Subclasses must define this method**
        """
        routespec = self.validate_routespec(routespec)
        service_alias = traefik_utils.generate_alias(routespec, "service")
        router_alias = traefik_utils.generate_alias(routespec, "router")

        async with self.mutex:
            # Pop each entry
            self.dynamic_config["http"]["routers"].pop(router_alias, None)
            self.dynamic_config["http"]["services"].pop(service_alias, None)
            self.dynamic_config["jupyter"]["routers"].pop(router_alias, None)

            self.persist_dynamic_config()

    async def get_all_routes(self):
        """Fetch and return all the routes associated by JupyterHub from the
        proxy.

        **Subclasses must define this method**

        Should return a dictionary of routes, where the keys are
        routespecs and each value is a dict of the form::

          {
            'routespec': the route specification ([host]/path/)
            'target': the target host URL (proto://host) for this route
            'data': the attached data dict for this route (as specified in add_route)
          }
        """
        all_routes = {}

        async with self.mutex:
            for router, value in self.dynamic_config["http"]["routers"].items():
                if router not in self.dynamic_config["jupyter"]["routers"]:
                    # Only check routers defined in jupyter node
                    continue
                escaped_routespec = "".join(router.split("_", 1)[1:])
                traefik_routespec = escapism.unescape(escaped_routespec)
                routespec = self.validate_routespec(traefik_routespec)
                all_routes.update(
                    {routespec: self._get_route_unsafe(traefik_routespec)}
                )

        return all_routes

    async def get_route(self, routespec):
        """Return the route info for a given routespec.

        Args:
            routespec (str):
                A URI that was used to add this route,
                e.g. `host.tld/path/`

        Returns:
            result (dict):
                dict with the following keys::

                'routespec': The normalized route specification passed in to add_route
                    ([host]/path/)
                'target': The target host for this route (proto://host)
                'data': The arbitrary data dict that was passed in by JupyterHub when adding this
                        route.

            None: if there are no routes matching the given routespec
        """
        routespec = self.validate_routespec(routespec)
        async with self.mutex:
            return self._get_route_unsafe(routespec)
