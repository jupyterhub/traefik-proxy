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

from urllib.parse import urlparse
from subprocess import Popen

from jupyterhub.proxy import Proxy


class TraefikProxy(Proxy):
    """JupyterHub Proxy implementation using traefik"""

    client = etcd3.client("127.0.0.1", 2379)
    traefik_port = 8000
    traefik = None
    prefix = "/traefik"
    jupyterhub_prefix = "/jupyterhub"

    def _setup_etcd(self):
        print("Seting up etcd...")
        self.client.put(self.prefix + "/debug", "true")
        self.client.put(self.prefix + "/defaultentrypoints/0", "http")
        self.client.put(self.prefix + "/entrypoints/http/address", ":8000")
        self.client.put(self.prefix + "/api/dashboard", "true")
        self.client.put(self.prefix + "/api/entrypoint", "http")
        self.client.put(self.prefix + "/loglevel", "ERROR")
        self.client.put(self.prefix + "/etcd/endpoint", "127.0.0.1:2379")
        self.client.put(self.prefix + "/etcd/prefix", self.prefix)
        self.client.put(self.prefix + "/etcd/useapiv3", "true")
        self.client.put(self.prefix + "/etcd/watch", "true")

    def _create_backend_alias_from_url(self, url):
        target = urlparse(url)
        return "jupyterhub_backend_" + target.netloc

    def _create_frontend_alias_from_url(self, url):
        target = urlparse(url)
        return "jupyterhub_frontend_" + target.netloc

    def _create_backend_url_path(self, backend_alias):
        return self.prefix + "/backends/" + backend_alias + "/servers/server1/url"

    def _create_backend_weight_path(self, backend_alias):
        return self.prefix + "/backends/" + backend_alias + "/servers/server1/weight"

    def _create_frontend_backend_path(self, frontend_alias):
        return self.prefix + "/frontends/" + frontend_alias + "/backend"

    def _create_frontend_rule_path(self, frontend_alias):
        return self.prefix + "/frontends/" + frontend_alias + "/routes/test/rule"

    async def start(self):
        """Start the proxy.

        Will be called during startup if should_start is True.

        **Subclasses must define this method**
        if the proxy is to be started by the Hub
        """

        # TODO check if there is another proxy process running
        self.traefik = Popen(["traefik", "--etcd", "--etcd.useapiv3=true"], stdout=None)
        # raise NotImplementedError()

    async def stop(self):
        """Stop the proxy.

        Will be called during teardown if should_start is True.

        **Subclasses must define this method**
        if the proxy is to be started by the Hub
        """
        # raise NotImplementedError()

        print(self.traefik.kill())
        print(self.traefik.wait())

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

        backend_alias = self._create_backend_alias_from_url(target)
        backend_url_path = self._create_backend_url_path(backend_alias)
        backend_weight_path = self._create_backend_weight_path(backend_alias)
        frontend_alias = self._create_frontend_alias_from_url(target)
        frontend_backend_path = self._create_frontend_backend_path(frontend_alias)
        frontend_rule_path = self._create_frontend_rule_path(frontend_alias)

        self.client.put(self.jupyterhub_prefix + routespec, target)
        # To be able to delete the route when routespec is provided
        encoded_data = data = json.dumps(data)
        self.client.put(target, encoded_data)
        # Store the data dict passed in by JupyterHub
        self.client.put(backend_url_path, target)
        self.client.put(backend_weight_path, "1")
        self.client.put(frontend_backend_path, backend_alias)
        self.client.put(frontend_rule_path, "PathPrefix:" + routespec)

    async def delete_route(self, routespec):
        """Delete a route with a given routespec if it exists.

        **Subclasses must define this method**
        """
        value, _ = self.client.get(self.jupyterhub_prefix + routespec)
        target = value.decode()

        self.client.delete(self.jupyterhub_prefix + routespec)
        self.client.delete(target)

        backend_alias = self._create_backend_alias_from_url(target)
        frontend_alias = self._create_frontend_alias_from_url(target)

        self.client.delete_prefix(self.prefix + "/backends/" + backend_alias)
        self.client.delete_prefix(self.prefix + "/frontends/" + frontend_alias)

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
        result = {}
        routes = self.client.get_prefix(self.jupyterhub_prefix)
        for value, metadata in routes:
            routespec = metadata.key.decode().replace(self.jupyterhub_prefix, "")
            target = value.decode()

            value, _ = self.client.get(target)
            data = value.decode()
            partial_res = {"routespec": routespec, "target": target, "data": data}

            result[routespec] = partial_res
        return result

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

        value, _ = self.client.get(self.jupyterhub_prefix + routespec)
        target = value.decode()
        value, _ = self.client.get(target)
        data = value.decode()
        result = {"routespec": routespec, "target": target, "data": data}

        return result
