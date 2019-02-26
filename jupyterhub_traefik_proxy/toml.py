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
import asyncio
import string
import escapism

from traitlets import Any, default, Unicode

from . import traefik_utils
from jupyterhub.proxy import Proxy
from jupyterhub_traefik_proxy import TraefikProxy


class TraefikTomlProxy(TraefikProxy):
    """JupyterHub Proxy implementation using traefik and toml config file"""

    mutex = Any()

    @default("mutex")
    def _default_mutex(self):
        return asyncio.Lock()

    toml_dynamic_config_file = Unicode(
        "rules.toml", config=True, help="""traefik's dynamic configuration file"""
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            # Load initial routing table from disk
            self.routes_cache = traefik_utils.load_routes(self.toml_dynamic_config_file)
        except FileNotFoundError:
            self.routes_cache = {}
        finally:
            if not self.routes_cache:
                self.routes_cache = {"backends": {}, "frontends": {}}

    async def _setup_traefik_static_config(self):
        await super()._setup_traefik_static_config()

        self.static_config["file"] = {"filename": "rules.toml", "watch": True}

        try:
            traefik_utils.persist_static_conf(
                self.toml_static_config_file, self.static_config
            )
            try:
                os.stat(self.toml_dynamic_config_file)
            except FileNotFoundError:
                # Make sure that the dynamic configuration file exists
                open(self.toml_dynamic_config_file, "a").close()
        except IOError:
            self.log.exception("Couldn't set up traefik's static config.")
            raise
        except:
            self.log.error("Couldn't set up traefik's static config. Unexpected error:")
            raise

    def _start_traefik(self):
        self.log.info("Starting traefik...")
        try:
            self._launch_traefik(config_type="toml")
        except FileNotFoundError as e:
            self.log.error(
                "Failed to find traefik \n"
                "The proxy can be downloaded from https://github.com/containous/traefik/releases/download."
            )
            raise

    def _clean_resources(self):
        try:
            if self.should_start:
                os.remove(self.toml_static_config_file)
            os.remove(self.toml_dynamic_config_file)
        except:
            self.log.error("Failed to remove traefik's configuration files")
            raise

    def _get_route_unsafe(self, routespec):
        safe = string.ascii_letters + string.digits + "_-"
        escaped_routespec = escapism.escape(routespec, safe=safe)
        result = {"data": "", "target": "", "routespec": routespec}

        def get_target_data(d, to_find):
            if to_find == "url":
                key = "target"
            else:
                key = to_find
            if result[key]:
                return
            for k, v in d.items():
                if k == to_find:
                    result[key] = v
                if isinstance(v, dict):
                    get_target_data(v, to_find)

        for key, value in self.routes_cache["backends"].items():
            if escaped_routespec in key:
                get_target_data(value, "url")
        for key, value in self.routes_cache["frontends"].items():
            if escaped_routespec in key:
                get_target_data(value, "data")
        if not result["data"] and not result["target"]:
            self.log.info("No route for {} found!".format(routespec))
            result = None
        else:
            result["data"] = json.loads(result["data"])
        return result

    async def start(self):
        """Start the proxy.

        Will be called during startup if should_start is True.

        **Subclasses must define this method**
        if the proxy is to be started by the Hub
        """
        await super().start()
        await self._wait_for_static_config(provider="file")

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
        routespec = self.validate_routespec(routespec)
        backend_alias = traefik_utils.generate_alias(routespec, "backend")
        frontend_alias = traefik_utils.generate_alias(routespec, "frontend")
        data = json.dumps(data)
        rule = traefik_utils.generate_rule(routespec)

        async with self.mutex:
            self.routes_cache["frontends"][frontend_alias] = {
                "backend": backend_alias,
                "passHostHeader": True,
                "routes": {"test": {"rule": rule, "data": data}},
            }

            self.routes_cache["backends"][backend_alias] = {
                "servers": {"server1": {"url": target, "weight": 1}}
            }
            traefik_utils.persist_routes(
                self.toml_dynamic_config_file, self.routes_cache
            )

        if self.should_start:
            try:
                # Check if traefik was launched
                pid = self.traefik_process.pid
            except AttributeError:
                self.log.error(
                    "You cannot add routes if the proxy isn't running! Please start the proxy: proxy.start()"
                )
                raise
        await self._wait_for_route(routespec, provider="file")

    async def delete_route(self, routespec):
        """Delete a route with a given routespec if it exists.

        **Subclasses must define this method**
        """
        routespec = self.validate_routespec(routespec)
        safe = string.ascii_letters + string.digits + "_-"
        escaped_routespec = escapism.escape(routespec, safe=safe)

        async with self.mutex:
            for key, value in self.routes_cache["frontends"].items():
                if escaped_routespec in key:
                    del self.routes_cache["frontends"][key]
                    break
            for key, value in self.routes_cache["backends"].items():
                if escaped_routespec in key:
                    del self.routes_cache["backends"][key]
                    break
        traefik_utils.persist_routes(self.toml_dynamic_config_file, self.routes_cache)

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
            for key, value in self.routes_cache["frontends"].items():
                escaped_routespec = "".join(key.split("_", 1)[1:])
                routespec = escapism.unescape(escaped_routespec)
                all_routes[routespec] = self._get_route_unsafe(routespec)

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
