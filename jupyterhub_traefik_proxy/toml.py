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
import toml

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

    toml_static_config_file = Unicode(
        "traefik.toml", config=True, help="""traefik's static configuration file"""
    )

    toml_dynamic_config_file = Unicode(
        "rules.toml", config=True, help="""traefik's dynamic configuration file"""
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.routes_cache = {}

    async def _setup_traefik_static_config(self):
        await super()._setup_traefik_static_config()

        self.static_config["file"] = {"filename": "rules.toml", "watch": True}

        try:
            with open(self.toml_static_config_file, "w") as f:
                toml.dump(self.static_config, f)
            # Make sure that the dynamic configuration file exists
            open(self.toml_dynamic_config_file, "a").close()
        except IOError:
            self.log.exception("Couldn't set up traefik's static config.")
        except:
            self.log.error(
                "Couldn't set up traefik's static config. Unexpected error:",
            )

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
            self.log.error("Failed to remove traefik's configuration files \n")
            raise

    def _get_route_unsafe(self, routespec):
        try:
            result = {
                "routespec": routespec,
                "target": self.routes_cache[routespec]["target"],
                "data": self.routes_cache[routespec]["data"],
            }
        except KeyError:
            self.log.info("No route for {} doesn't exist!".format(routespec))
            result = None
        finally:
            return result

    def _persist_routes(self):
        with traefik_utils.atomic_writing(self.toml_dynamic_config_file) as config_fd:
            config_fd.write("[frontends]\n")
            for key, value in self.routes_cache.items():
                config_fd.write("".join(value["frontend"]))
            config_fd.write("[backends]\n")
            for key, value in self.routes_cache.items():
                config_fd.write("".join(value["backend"]))

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

        self.log.info("Adding route for %s to %s.", routespec, target)

        route_keys = traefik_utils.generate_route_keys(
            self, target, routespec, separator="."
        )
        data = json.dumps(data)
        rule = traefik_utils.generate_rule(routespec)

        async with self.mutex:
            self.routes_cache[routespec] = {
                "backend": [
                    "[backends." + route_keys.backend_alias + "]\n",
                    "[" + route_keys.backend_url_path + "]\n",
                    "url = " + '"' + target + '"\n',
                    "weight = " + "1\n",
                ],
                "frontend": [
                    "[frontends." + route_keys.frontend_alias + "]\n",
                    "backend = " + '"' + route_keys.backend_alias + '"\n',
                    "passHostHeader = true\n",
                    "[" + route_keys.frontend_rule_path + "]\n",
                    "rule = " + '"' + rule + '"\n',
                    "data = " + "'" + data + "'\n",
                ],
                "data": data,
                "target": target,
            }
            self._persist_routes()

        try:
            # Check if traefik was launched
            pid = self.traefik_process.pid
            await self._wait_for_route(target, provider="file")
        except AttributeError:
            self.log.error(
                "You cannot add routes if the proxy isn't running! Please start the proxy: proxy.start()"
            )
            raise

    async def delete_route(self, routespec):
        """Delete a route with a given routespec if it exists.

        **Subclasses must define this method**
        """
        async with self.mutex:
            del self.routes_cache[routespec]
            self._persist_routes()

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
        await self.mutex.acquire()
        try:
            for key, value in self.routes_cache.items():
                all_routes[key] = self._get_route_unsafe(key)
        finally:
            self.mutex.release()

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
        await self.mutex.acquire()
        try:
            result = self._get_route_unsafe(routespec)
        finally:
            self.mutex.release()
        return result
