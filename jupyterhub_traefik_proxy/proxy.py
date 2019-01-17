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

from jupyterhub.proxy import Proxy
from jupyterhub.utils import exponential_backoff
from . import traefik_utils

from traitlets import Any, Unicode
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from subprocess import Popen
from os.path import abspath, dirname, join
from urllib.parse import urlparse

import json


class TraefikProxy(Proxy):
    """JupyterHub Proxy implementation using traefik"""

    traefik_process = Any()

    traefik_api_url = Unicode(
        "http://127.0.0.1:8099",
        config=True,
        help="""traefik authenticated api endpoint url""",
    )

    traefik_api_password = Unicode(
        config=True, help="""The password for traefik api login"""
    )

    traefik_api_username = Unicode(
        config=True, help="""The username for traefik api login"""
    )

    traefik_api_hashed_password = Unicode()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.static_config = {}

    def _generate_htpassword(self):
        from passlib.apache import HtpasswdFile

        ht = HtpasswdFile()
        ht.set_password(self.traefik_api_username, self.traefik_api_password)
        self.traefik_api_hashed_password = str(ht.to_string()).split(":")[1][:-3]

    async def _wait_for_route(self, routespec, provider):
        async def _check_traefik_dynamic_conf_ready():
            """ Check if traefik loaded its dynamic configuration from the
                etcd cluster """
            expected_backend = traefik_utils.generate_alias(routespec, "backend")
            expected_frontend = traefik_utils.generate_alias(routespec, "frontend")
            ready = False
            try:
                resp_backends = await AsyncHTTPClient().fetch(
                    self.traefik_api_url + "/api/providers/" + provider + "/backends",
                    auth_username=self.traefik_api_username,
                    auth_password=self.traefik_api_password,
                )
                resp_frontends = await AsyncHTTPClient().fetch(
                    self.traefik_api_url + "/api/providers/" + provider + "/frontends",
                    auth_username=self.traefik_api_username,
                    auth_password=self.traefik_api_password,
                )
                backends_data = json.loads(resp_backends.body)
                frontends_data = json.loads(resp_frontends.body)

                if resp_backends.code == 200 and resp_frontends.code == 200:
                    ready = (
                        expected_backend in backends_data
                        and expected_frontend in frontends_data
                    )
            except Exception as e:
                backends_rc, frontends_rc = e.response.code
                ready = False
            finally:
                return ready

        await exponential_backoff(
            _check_traefik_dynamic_conf_ready,
            "Traefik route for %s configuration not available" % routespec,
            timeout=20,
        )

    async def _wait_for_static_config(self, provider):
        async def _check_traefik_static_conf_ready():
            """ Check if traefik loaded its static configuration from the
            etcd cluster """
            try:
                resp = await AsyncHTTPClient().fetch(
                    self.traefik_api_url + "/api/providers/" + provider,
                    auth_username=self.traefik_api_username,
                    auth_password=self.traefik_api_password,
                )
                rc = resp.code
            except ConnectionRefusedError:
                rc = None
            except Exception as e:
                rc = e.response.code
            finally:
                return rc == 200

        await exponential_backoff(
            _check_traefik_static_conf_ready,
            "Traefik static configuration not available",
            timeout=20,
        )

    def _stop_traefik(self):
        self.log.info("Cleaning up proxy[%i]...", self.traefik_process.pid)
        self.traefik_process.kill()
        self.traefik_process.wait()

    def _launch_traefik(self, config_type):
        if config_type == "toml":
            config_file_path = abspath(join(dirname(__file__), "traefik.toml"))
            self.traefik_process = Popen(
                ["traefik", "-c", config_file_path], stdout=None
            )
        elif config_type == "etcd":
            self.traefik_process = Popen(
                ["traefik", "--etcd", "--etcd.useapiv3=true"], stdout=None
            )
        else:
            raise ValueError(
                "Configuration mode not supported \n.\
                The proxy can only be configured through toml and etcd"
            )

    async def _setup_traefik_static_config(self):
        self.log.info("Setting up traefik's static config...")
        self._generate_htpassword()

        self.static_config = {}
        self.static_config["defaultentrypoints"] = ["http"]
        self.static_config["debug"] = True
        self.static_config["logLevel"] = "ERROR"
        entryPoints = {}
        entryPoints["http"] = {"address": ":" + str(urlparse(self.public_url).port)}
        auth = {
            "basic": {
                "users": [
                    self.traefik_api_username + ":" + self.traefik_api_hashed_password
                ]
            }
        }
        entryPoints["auth_api"] = {
            "address": ":" + str(urlparse(self.traefik_api_url).port),
            "auth": auth,
        }
        self.static_config["entryPoints"] = entryPoints
        self.static_config["api"] = {"dashboard": True, "entrypoint": "auth_api"}
        self.static_config["wss"] = {"protocol": "http"}

    async def start(self):
        """Start the proxy.

        Will be called during startup if should_start is True.

        **Subclasses must define this method**
        if the proxy is to be started by the Hub
        """
        self._start_traefik()
        await self._setup_traefik_static_config()

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
        raise NotImplementedError()

    async def delete_route(self, routespec):
        """Delete a route with a given routespec if it exists.

        **Subclasses must define this method**
        """
        raise NotImplementedError()

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
        raise NotImplementedError()

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
        raise NotImplementedError()
