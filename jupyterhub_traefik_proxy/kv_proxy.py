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

from traitlets import Any, Unicode

from . import traefik_utils
from jupyterhub_traefik_proxy import TraefikProxy


class TKvProxy(TraefikProxy):
    """
    JupyterHub Proxy implementation using traefik and a key-value store.
    Custom proxy implementations based on trafik and a key-value store
    can sublass :class:`TKvProxy`.
    """

    kv_client = Any()
    # Key-value store client

    kv_name = Unicode(config=False, help="""The name of the key value store""")

    kv_username = Unicode(
        config=True, help="""The username for key value store login"""
    )

    kv_password = Unicode(
        config=True, help="""The password for key value store login"""
    )

    kv_url = Unicode(config=True, help="""The URL of the key value store server""")

    kv_traefik_prefix = traefik_utils.KVStorePrefix(
        config=True,
        help="""The key value store key prefix for traefik static configuration""",
    )

    kv_jupyterhub_prefix = Unicode(
        config=True,
        help="""The key value store key prefix for traefik dynamic configuration""",
    )

    def _define_kv_specific_static_config(self):
        """Define the traefik static configuration that configures
        traefik's communication with the key-value store.

        Will be called during startup if should_start is True.

        **Subclasses must define this method**
        if the proxy is to be started by the Hub.

        In order to be picked up by the proxy, the static configuration
        must be stored into `proxy.static_config` dict under the `kv_name` key.
        """
        raise NotImplementedError()

    async def _kv_atomic_add_route_parts(
        self, jupyterhub_routespec, target, data, route_keys, rule
    ):
        """Add the key-value pairs associated with a route within a
        key-value store transaction.

        **Subclasses must define this method**

        Will be called during add_route.

        When retrieving or deleting a route, the parts of a route
        are expected to have the following structure:
        [ key: jupyterhub_routespec            , value: target ]
        [ key: target                          , value: data   ]
        [ key: route_keys.backend_url_path     , value: target ]
        [ key: route_keys.frontend_rule_path   , value: rule   ]
        [ key: route_keys.frontend_backend_path, value:
                                       route_keys.backend_alias]
        [ key: route_keys.backend_weight_path  , value: w(int) ]
            (where `w` is the weight of the backend to be used during load balancing)

        Returns:
            result (tuple):
                'status'(int): The transaction status
                    (0: failure, positive: success)
                'response'(str): The transaction response
        """
        raise NotImplementedError()

    async def _kv_atomic_delete_route_parts(self, jupyterhub_routespec, route_keys):
        """Delete the key-value pairs associated with a route within a
        key-value store transaction (if the route exists).

        **Subclasses must define this method**

        Will be called during delete_route.

        The keys associated with a route are:
            jupyterhub_routespec,
            target,
            route_keys.backend_url_path,
            route_keys.frontend_rule_path,
            route_keys.frontend_backend_path,
            route_keys.backend_weight_path,

        Returns:
            result (tuple):
                'status'(int): The transaction status
                    (0: failure, positive: success).
                'response'(str): The transaction response.
        """
        raise NotImplementedError()

    async def _kv_get_target(self, jupyterhub_routespec):
        """Retrive the target from the key-value store.
        The target is the value associated with `jupyterhub_routespec` key.

        **Subclasses must define this method**

        Returns:
            target (str): The full URL associated with this route.
        """
        raise NotImplementedError()

    async def _kv_get_data(self, target):
        """Retrive the data associated with the `target` from the key-value store.

        **Subclasses must define this method**

        Returns:
            data (dict): A JSONable dict that holds extra info about the route
        """
        raise NotImplementedError()

    async def _kv_get_route_parts(self, kv_entry):
        """Retrive all the parts that make up a route (i.e. routespec, target, data)
        from the key-value store given a `kv_entry`.

        A `kv_entry` is a key-value store entry where the key starts with
        `proxy.jupyterhub_prefix`. It is expected that only the routespecs
        will be prefixed with `proxy.jupyterhub_prefix` when added to the kv store.

        **Subclasses must define this method**

        Returns:
            'routespec': The normalized route specification passed in to add_route
                ([host]/path/)
            'target': The target host for this route (proto://host)
            'data': The arbitrary data dict that was passed in by JupyterHub when adding this
                route.
        """
        raise NotImplementedError()

    async def _kv_get_jupyterhub_prefixed_entries(self):
        """Retrive from the kv store all the key-value pairs where the key starts with
        `proxy.jupyterhub_prefix`.
        It is expected that only the routespecs will be prefixed with `proxy.jupyterhub_prefix`
        when added to the kv store.

        **Subclasses must define this method**

        Returns:
            'routes': A list of key-value store entries where the keys start
                with `proxy.jupyterhub_prefix`.
        """

        raise NotImplementedError()

    def _clean_resources(self):
        try:
            if self.should_start:
                os.remove(self.toml_static_config_file)
        except:
            self.log.error("Failed to remove traefik's configuration files")
            raise

    def _start_traefik(self):
        self.log.info("Starting traefik...")
        try:
            self._launch_traefik(config_type=self.kv_name)
        except FileNotFoundError as e:
            self.log.error(
                "Failed to find traefik \n"
                "The proxy can be downloaded from https://github.com/containous/traefik/releases/download."
            )
            raise

    async def _setup_traefik_static_config(self):
        await super()._setup_traefik_static_config()
        self._define_kv_specific_static_config()
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

    async def start(self):
        """Start the proxy.
        Will be called during startup if should_start is True.
        """
        await super().start()
        await self._wait_for_static_config(provider=self.kv_name)

    async def stop(self):
        """Stop the proxy.
        Will be called during teardown if should_start is True.
        """
        await super().stop()
        self._clean_resources()

    async def add_route(self, routespec, target, data):
        """Add a route to the proxy.

        Args:
            routespec (str): A URL prefix ([host]/path/) for which this route will be matched,
                e.g. host.name/path/
            target (str): A full URL that will be the target of this route.
            data (dict): A JSONable dict that will be associated with this route, and will
                be returned when retrieving information about this route.

        Will raise an appropriate Exception (FIXME: find what?) if the route could
        not be added.

        This proxy implementation prefixes the routespec with `proxy.jupyterhub_prefix` when
        adding it to the kv store in orde to associate the fact that the route came from JupyterHub.
        Everything traefik related is prefixed with `proxy.traefik_prefix`.
        """
        self.log.info("Adding route for %s to %s.", routespec, target)

        routespec = self.validate_routespec(routespec)
        route_keys = traefik_utils.generate_route_keys(self, routespec)

        # Store the data dict passed in by JupyterHub
        data = json.dumps(data)
        # Generate the routing rule
        rule = traefik_utils.generate_rule(routespec)

        # To be able to delete the route when only routespec is provided
        jupyterhub_routespec = self.kv_jupyterhub_prefix + routespec

        status, response = await self._kv_atomic_add_route_parts(
            jupyterhub_routespec, target, data, route_keys, rule
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

        await self._wait_for_route(routespec, provider=self.kv_name)

    async def delete_route(self, routespec):
        """Delete a route and all the traefik related info associated given a routespec,
        (if it exists).
        """
        routespec = self.validate_routespec(routespec)
        jupyterhub_routespec = self.kv_jupyterhub_prefix + routespec
        route_keys = traefik_utils.generate_route_keys(self, routespec)

        status, response = await self._kv_atomic_delete_route_parts(
            jupyterhub_routespec, route_keys
        )

        if status:
            self.log.info("Routespec %s was deleted.", routespec)
        else:
            self.log.error(
                "Couldn't delete route %s. Response: %s", routespec, response
            )

    async def get_all_routes(self):
        """Fetch and return all the routes associated by JupyterHub from the
        proxy.

        Returns a dictionary of routes, where the keys are
        routespecs and each value is a dict of the form::

          {
            'routespec': the route specification ([host]/path/)
            'target': the target host URL (proto://host) for this route
            'data': the attached data dict for this route (as specified in add_route)
          }
        """
        all_routes = {}
        routes = await self._kv_get_jupyterhub_prefixed_entries()

        for kv_entry in routes:
            routespec, target, data = await self._kv_get_route_parts(kv_entry)
            all_routes[routespec] = {
                "routespec": routespec,
                "target": target,
                "data": None if data is None else json.loads(data),
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
        jupyterhub_routespec = self.kv_jupyterhub_prefix + routespec

        target = await self._kv_get_target(jupyterhub_routespec)
        if target is None:
            return None
        data = await self._kv_get_data(target)

        return {
            "routespec": routespec,
            "target": target,
            "data": None if data is None else json.loads(data),
        }
