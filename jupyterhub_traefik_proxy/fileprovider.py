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


class TraefikFileProviderProxy(TraefikProxy):
    """JupyterHub Proxy implementation using traefik and toml or yaml config file"""

    mutex = Any()

    @default("mutex")
    def _default_mutex(self):
        return asyncio.Lock()

    dynamic_config_file = Unicode(
        "rules.toml", config=True, help="""traefik's dynamic configuration file"""
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        try:
            # Load initial routing table from disk
            self.routes_cache = traefik_utils.load_routes(self.dynamic_config_file)
        except FileNotFoundError:
            self.routes_cache = {}

        if not self.routes_cache:
            self.routes_cache = {
                "http" : {"services": {}, "routers": {}},
                "jupyter": {"routers" : {} }
            }

    async def _setup_traefik_static_config(self):
        await super()._setup_traefik_static_config()

        # Is this not the same as the dynamic config file?
        self.static_config["file"] = {"filename": "rules.toml", "watch": True}

        try:
            traefik_utils.persist_static_conf(
                self.static_config_file, self.static_config
            )
            try:
                os.stat(self.dynamic_config_file)
            except FileNotFoundError:
                # Make sure that the dynamic configuration file exists
                self.log.info(
                    f"Creating the dynamic configuration file: {self.dynamic_config_file}"
                )
                open(self.dynamic_config_file, "a").close()
        except IOError:
            self.log.exception("Couldn't set up traefik's static config.")
            raise
        except:
            self.log.error("Couldn't set up traefik's static config. Unexpected error:")
            raise

    def _start_traefik(self):
        self.log.info("Starting traefik...")
        try:
            self._launch_traefik(config_type="fileprovider")
        except FileNotFoundError as e:
            self.log.error(
                "Failed to find traefik \n"
                "The proxy can be downloaded from https://github.com/containous/traefik/releases/download."
            )
            raise

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
        routespec = self._routespec_from_traefik_path(traefik_routespec)
        result = {"data": None, "target": None, "routespec": routespec}

        def get_target_data(d, to_find):
            if to_find == "url":
                key = "target"
            else:
                key = to_find
            if result[key] is not None:
                return
            for k, v in d.items():
                if k == to_find:
                    result[key] = v
                if isinstance(v, dict):
                    get_target_data(v, to_find)

        service_node = self.routes_cache["http"]["services"].get(service_alias, None)
        if service_node is not None:
            get_target_data(service_node, "url")

        router_node = self.routes_cache["jupyter"]["routers"].get(router_alias, None)
        if router_node is not None:
            get_target_data(router_node, "data")

        if result["data"] is None and result["target"] is None:
            self.log.info("No route for {} found!".format(routespec))
            result = None
        self.log.debug("treefik routespec: {0}".format(traefik_routespec))
        self.log.debug("result for routespec {0}:-\n{1}".format(routespec, result))

        # No longer bother converting `data` to/from JSON
        #else:
        #    result["data"] = json.loads(result["data"])

        #if service_alias in self.routes_cache["services"]:
        #    get_target_data(self.routes_cache["services"][service_alias], "url")

        #if router_alias in self.routes_cache["routers"]:
        #    get_target_data(self.routes_cache["routers"][router_alias], "data")

        #if not result["data"] and not result["target"]:
        #    self.log.info("No route for {} found!".format(routespec))
        #    result = None
        #else:
        #    result["data"] = json.loads(result["data"])
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
                FIXME: Why do we need to pass data back and forth to traefik?
                       Traefik v2 doesn't seem to allow a data key...

        Will raise an appropriate Exception (FIXME: find what?) if the route could
        not be added.

        The proxy implementation should also have a way to associate the fact that a
        route came from JupyterHub.
        """
        traefik_routespec = self._routespec_to_traefik_path(routespec)
        service_alias = traefik_utils.generate_alias(traefik_routespec, "service")
        router_alias = traefik_utils.generate_alias(traefik_routespec, "router")
        #data = json.dumps(data)
        rule = traefik_utils.generate_rule(traefik_routespec)

        async with self.mutex:
            self.routes_cache["http"]["routers"][router_alias] = {
                "service": service_alias,
                "rule": rule,
                # The data node is passed by JupyterHub. We can store its data in our routes_cache,
                # but giving it to Traefik causes issues...
                #"data" : data
                #"routes": {"test": {"rule": rule, "data": data}},
            }

            # Add the data node to a separate top-level node
            self.routes_cache["jupyter"]["routers"][router_alias] = {"data": data}

            self.routes_cache["http"]["services"][service_alias] = {
                "loadBalancer" : {
                    "servers": {"server1": {"url": target} },
                    "passHostHeader": True
                }
            }
            traefik_utils.persist_routes(
                self.dynamic_config_file, self.routes_cache
            )

        self.log.debug("treefik routespec: {0}".format(traefik_routespec))
        self.log.debug("data for routespec {0}:-\n{1}".format(routespec, data))

        if self.should_start:
            try:
                # Check if traefik was launched
                pid = self.traefik_process.pid
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
        routespec = self._routespec_to_traefik_path(routespec)
        service_alias = traefik_utils.generate_alias(routespec, "service")
        router_alias = traefik_utils.generate_alias(routespec, "router")

        async with self.mutex:
            self.routes_cache["http"]["routers"].pop(router_alias, None)
            self.routes_cache["http"]["services"].pop(service_alias, None)

        traefik_utils.persist_routes(self.dynamic_config_file, self.routes_cache)

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
            for key, value in self.routes_cache["http"]["routers"].items():
                escaped_routespec = "".join(key.split("_", 1)[1:])
                traefik_routespec = escapism.unescape(escaped_routespec)
                routespec = self._routespec_from_traefik_path(traefik_routespec)
                all_routes.update({
                  routespec : self._get_route_unsafe(traefik_routespec)
                })

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
        routespec = self._routespec_to_traefik_path(routespec)
        async with self.mutex:
            return self._get_route_unsafe(routespec)

