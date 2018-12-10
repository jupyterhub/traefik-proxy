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
import json
import etcd3
import os

from subprocess import Popen

from traitlets import Any, default, Unicode

from jupyterhub.proxy import Proxy

from . import traefik_utils


class TraefikEtcdProxy(Proxy):
    """JupyterHub Proxy implementation using traefik and etcd"""

    traefik_process = Any()
    client = Any()

    @default("client")
    def _default_client(self):
        return etcd3.client("127.0.0.1", 2379)

    command = "traefik"
    traefik_port = traefik_utils.get_port(command)

    etcd_traefik_prefix = Unicode(
        "/traefik/",
        config=True,
        help="""the etcd key prefix for traefik configuration""",
    )

    etcd_jupyterhub_prefix = Unicode(
        "/jupyterhub/",
        config=True,
        help="""the etcd key prefix for traefik configuration""",
    )

    def _setup_etcd(self):
        self.log.info("Seting up etcd...")
        self.client.put(self.etcd_traefik_prefix + "debug", "true")
        self.client.put(self.etcd_traefik_prefix + "defaultentrypoints/0", "http")
        self.client.put(
            self.etcd_traefik_prefix + "entrypoints/http/address",
            ":" + str(self.traefik_port),
        )
        self.client.put(self.etcd_traefik_prefix + "api/dashboard", "true")
        self.client.put(self.etcd_traefik_prefix + "api/entrypoint", "http")
        self.client.put(self.etcd_traefik_prefix + "loglevel", "ERROR")
        self.client.put(self.etcd_traefik_prefix + "etcd/endpoint", "127.0.0.1:2379")
        self.client.put(
            self.etcd_traefik_prefix + "etcd/prefix", self.etcd_traefik_prefix
        )
        self.client.put(self.etcd_traefik_prefix + "etcd/useapiv3", "true")
        self.client.put(self.etcd_traefik_prefix + "etcd/watch", "true")
        self.client.put(self.etcd_traefik_prefix + "providersThrottleDuration", "1")

    def _start_traefik(self):
        self.log.info("Starting %s proxy...", self.command)
        try:
            self.traefik_process = traefik_utils.launch_traefik_with_etcd()
        except FileNotFoundError as e:
            self.log.error(
                "Failed to find proxy %s\n"
                "The proxy can be downloaded from https://github.com/containous/traefik/releases/download."
                % self.command
            )
            raise

    def _stop_traefik(self):
        self.log.info("Cleaning up proxy[%i]...", self.traefik_process.pid)
        self.traefik_process.kill()


    async def start(self):
        """Start the proxy.

        Will be called during startup if should_start is True.

        **Subclasses must define this method**
        if the proxy is to be started by the Hub
        """
        # TODO: investigate deploying a traefik cluster instead of a single instance!
        self._start_traefik()
        self._setup_etcd()

    async def stop(self):
        """Stop the proxy.

        Will be called during teardown if should_start is True.

        **Subclasses must define this method**
        if the proxy is to be started by the Hub
        """
        self._stop_traefik()

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

        backend_alias = traefik_utils.create_backend_alias_from_url(target)
        backend_url_path = traefik_utils.create_backend_url_path(self, backend_alias)
        backend_weight_path = traefik_utils.create_backend_weight_path(
            self, backend_alias
        )
        frontend_alias = traefik_utils.create_frontend_alias_from_url(target)
        frontend_backend_path = traefik_utils.create_frontend_backend_path(
            self, frontend_alias
        )
        frontend_rule_path = traefik_utils.create_frontend_rule_path(
            self, frontend_alias
        )

        # To be able to delete the route when routespec is provided
        jupyterhub_routespec = self.etcd_jupyterhub_prefix + routespec
        self.client.put(jupyterhub_routespec, target)

        # Store the data dict passed in by JupyterHub
        encoded_data = data = json.dumps(data)
        self.client.put(target, encoded_data)

        self.log.info("Adding backend %s with the alias.", target, backend_alias)
        self.client.put(backend_url_path, target)
        self.client.put(backend_weight_path, "1")

        self.log.info(
            "Adding frontend %s for backend %s with the following routing rule %s.",
            frontend_alias,
            backend_alias,
            routespec,
        )

        self.client.put(frontend_backend_path, backend_alias)
        if routespec.startswith("/"):
            # Path-based route, e.g. /proxy/path/
            rule = "PathPrefix:" + routespec
        else:
            # Host-based routing, e.g. host.tld/proxy/path/
            host, path_prefix = routespec.split("/", 1)
            path_prefix = "/" + path_prefix
            rule = "Host:" + host + ";PathPrefix:" + path_prefix

        self.client.put(frontend_rule_path, rule)

    async def delete_route(self, routespec):
        """Delete a route with a given routespec if it exists.

        **Subclasses must define this method**
        """
        jupyterhub_routespec = self.etcd_jupyterhub_prefix + routespec
        value, _ = self.client.get(jupyterhub_routespec)
        if value is None:
            self.log.warning("Route %s doesn't exist. Nothing to delete", routespec)
            return

        target = value.decode()
        if self.client.delete(jupyterhub_routespec) is False:
            self.log.error("Couldn't delete %s.", routespec)
        if self.client.delete(target) is False:
            self.log.error("Couldn't delete %s.", routespec)

        backend_alias = traefik_utils.create_backend_alias_from_url(target)
        frontend_alias = traefik_utils.create_frontend_alias_from_url(target)

        self.log.info(
            'Deleting %s and %s associated with the the routespec "%s".',
            frontend_alias,
            backend_alias,
            routespec,
        )
        self.client.delete_prefix(
            self.etcd_traefik_prefix + "backends/" + backend_alias
        )
        self.client.delete_prefix(
            self.etcd_traefik_prefix + "frontends/" + frontend_alias
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
        routes = self.client.get_prefix(self.etcd_jupyterhub_prefix)

        for value, metadata in routes:
            # Strip the "/jupyterhub" prefix from the routespec
            routespec = metadata.key.decode().replace(self.etcd_jupyterhub_prefix, "")
            target = value.decode()

            value, _ = self.client.get(target)
            if value is None:
                data = None
            else:
                data = value.decode()

            all_routes[routespec] = {
                "routespec": routespec,
                "target": target,
                "data": data,
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
        jupyterhub_routespec = self.etcd_jupyterhub_prefix + routespec
        value, _ = self.client.get(jupyterhub_routespec)
        if value == None:
            return None
        target = value.decode()
        value, _ = self.client.get(target)
        if value is None:
            data = None
        else:
            data = value.decode()

        result = {"routespec": routespec, "target": target, "data": data}
        return result
