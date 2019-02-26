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
from jupyterhub_traefik_proxy import TraefikProxy


class TraefikEtcdProxy(TraefikProxy):
    """JupyterHub Proxy implementation using traefik and etcd"""

    executor = Any()

    @default("executor")
    def _default_executor(self):
        return ThreadPoolExecutor(1)

    etcd_client = Any()

    etcd_username = Unicode(config=True, help="""The username for etcd login""")

    etcd_password = Unicode(config=True, help="""The password for etcd login""")

    @default("etcd_client")
    def _default_client(self):
        etcd_service = urlparse(self.etcd_url)
        if self.etcd_password:
            return etcd3.client(
                host=str(etcd_service.hostname),
                port=etcd_service.port,
                user=self.etcd_username,
                password=self.etcd_password,
            )
        else:
            return etcd3.client(host=str(etcd_service.hostname), port=etcd_service.port)

    etcd_url = Unicode(
        "http://127.0.0.1:2379", config=True, help="""The URL of the etcd server"""
    )

    etcd_traefik_prefix = Unicode(
        "/traefik/",
        config=True,
        help="""The etcd key prefix for traefik static configuration""",
    )

    etcd_jupyterhub_prefix = Unicode(
        "/jupyterhub/",
        config=True,
        help="""The etcd key prefix for traefik dynamic configuration""",
    )

    @run_on_executor
    def _etcd_transaction(self, success_actions):
        status, response = self.etcd_client.transaction(
            compare=[], success=success_actions, failure=[]
        )
        return status, response

    @run_on_executor
    def _etcd_get(self, key):
        value, _ = self.etcd_client.get(key)
        return value

    @run_on_executor
    def _etcd_get_prefix(self, prefix):
        routes = self.etcd_client.get_prefix(prefix)
        return routes

    async def _setup_traefik_static_config(self):
        await super()._setup_traefik_static_config()

        self.static_config["etcd"] = {
            "username": self.etcd_username,
            "password": self.etcd_password,
            "endpoint": str(urlparse(self.etcd_url).hostname)
            + ":"
            + str(urlparse(self.etcd_url).port),
            "prefix": self.etcd_traefik_prefix,
            "useapiv3": True,
            "watch": True,
            "providersThrottleDuration": 1,
        }

        try:
            traefik_utils.persist_static_conf(
                self.toml_static_config_file, self.static_config
            )
        except IOError:
            self.log.exception("Couldn't set up traefik's static config.")
            raise
        except:
            self.log.error("Couldn't set up traefik's static config. Unexpected error:")
            raise

    def _start_traefik(self):
        self.log.info("Starting traefik...")
        try:
            self._launch_traefik(config_type="etcd")
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
        except:
            self.log.error("Failed to remove traefik's configuration files")
            raise

    async def start(self):
        """Start the proxy.

        Will be called during startup if should_start is True.

        **Subclasses must define this method**
        if the proxy is to be started by the Hub
        """
        # TODO: investigate deploying a traefik cluster instead of a single instance!
        await super().start()
        await self._wait_for_static_config(provider="etcdv3")

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

        routespec = self.validate_routespec(routespec)
        route_keys = traefik_utils.generate_route_keys(self, routespec)

        # Store the data dict passed in by JupyterHub
        data = json.dumps(data)
        rule = traefik_utils.generate_rule(routespec)

        # To be able to delete the route when routespec is provided
        jupyterhub_routespec = self.etcd_jupyterhub_prefix + routespec

        success = [
            self.etcd_client.transactions.put(jupyterhub_routespec, target),
            self.etcd_client.transactions.put(target, data),
            self.etcd_client.transactions.put(route_keys.backend_url_path, target),
            self.etcd_client.transactions.put(route_keys.backend_weight_path, "1"),
            self.etcd_client.transactions.put(
                route_keys.frontend_backend_path, route_keys.backend_alias
            ),
            self.etcd_client.transactions.put(route_keys.frontend_rule_path, rule),
        ]

        status, response = await maybe_future(self._etcd_transaction(success))

        if status:
            self.log.info(
                "Added backend %s with the alias %s.", target, route_keys.backend_alias
            )
            self.log.info(
                "Added frontend %s for backend %s with the following routing rule %s.",
                route_keys.frontend_alias,
                route_keys.backend_alias,
                routespec,
            )
        else:
            self.log.error(
                "Couldn't add route for %s. Response: %s", routespec, response
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
        await self._wait_for_route(routespec, provider="etcdv3")

    async def delete_route(self, routespec):
        """Delete a route with a given routespec if it exists.

        **Subclasses must define this method**
        """
        routespec = self.validate_routespec(routespec)
        jupyterhub_routespec = self.etcd_jupyterhub_prefix + routespec
        value = await maybe_future(self._etcd_get(jupyterhub_routespec))
        if value is None:
            self.log.warning("Route %s doesn't exist. Nothing to delete", routespec)
            return

        target = value.decode()
        route_keys = traefik_utils.generate_route_keys(self, routespec)

        success = [
            self.etcd_client.transactions.delete(jupyterhub_routespec),
            self.etcd_client.transactions.delete(target),
            self.etcd_client.transactions.delete(route_keys.backend_url_path),
            self.etcd_client.transactions.delete(route_keys.backend_weight_path),
            self.etcd_client.transactions.delete(route_keys.frontend_backend_path),
            self.etcd_client.transactions.delete(route_keys.frontend_rule_path),
        ]
        status, response = await maybe_future(self._etcd_transaction(success))

        if status:
            self.log.info("Routespec %s was deleted.", routespec)
        else:
            self.log.error(
                "Couldn't delete route %s. Response: %s", routespec, response
            )

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
        routes = await maybe_future(self._etcd_get_prefix(self.etcd_jupyterhub_prefix))

        for value, metadata in routes:
            # Strip the "/jupyterhub" prefix from the routespec
            routespec = metadata.key.decode().replace(self.etcd_jupyterhub_prefix, "")
            target = value.decode()

            value = await maybe_future(self._etcd_get(target))
            if value is None:
                data = None
            else:
                data = value

            all_routes[routespec] = {
                "routespec": routespec,
                "target": target,
                "data": json.loads(data),
            }

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
        jupyterhub_routespec = self.etcd_jupyterhub_prefix + routespec

        value = await maybe_future(self._etcd_get(jupyterhub_routespec))
        if value == None:
            return None
        target = value.decode()
        value = await maybe_future(self._etcd_get(target))
        if value is None:
            data = None
        else:
            data = value

        return {"routespec": routespec, "target": target, "data": json.loads(data)}
