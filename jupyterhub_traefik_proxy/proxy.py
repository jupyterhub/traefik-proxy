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
from os.path import abspath, dirname, join
from subprocess import Popen, TimeoutExpired
import asyncio.subprocess
from urllib.parse import urlparse

from traitlets import Any, Bool, Dict, Integer, List, Unicode, default, observe
from tornado.httpclient import AsyncHTTPClient

from jupyterhub.utils import exponential_backoff, url_path_join, new_token
from jupyterhub.proxy import Proxy
from . import traefik_utils


class TraefikProxy(Proxy):
    """JupyterHub Proxy implementation using traefik"""

    traefik_process = Any()

    static_config_file = Unicode(
        "traefik.toml", config=True, help="""traefik's static configuration file"""
    )

    static_config = Dict()
    dynamic_config = Dict()

    traefik_api_url = Unicode(
        "http://localhost:8099",
        config=True,
        help="""traefik authenticated api endpoint url""",
    )

    traefik_api_validate_cert = Bool(
        True,
        config=True,
        help="""validate SSL certificate of traefik api endpoint""",
    )

    debug = Bool(False, config=True, help="""Debug the proxy class?""")

    traefik_log_level = Unicode(config=True, help="""traefik's log level""")
    log_level = Unicode(config=True, help="""The Proxy's log level""")

    traefik_api_password = Unicode(
        config=True, help="""The password for traefik api login"""
    )

    provider_name = Unicode(
        config=True, help="""The provider name that Traefik expects, e.g. file, consul, etcd"""
    )

    # FIXME: How best to enable TLS on routers assigned to only select
    # entrypoints defined here?
    traefik_entrypoints = List(
        trait=Unicode(), config=True,
        help="""A list of entrypoint names, to which each Traefik router is assigned"""
    )

    default_entrypoint = Unicode(
        "web", config=True,
        help="""Default entrypoint to apply to jupyterhub-configured traefik routers"""
    )

    @observe("default_entrypoint", type="change")
    def _update_entrypoints(self, change):
        """Update the list of traefik_entrypoints, should default_entrypoint be changed"""
        if change["old"] in self.traefik_entrypoints:
            self.traefik_entrypoints.remove(change["old"])
        if change["new"] not in self.traefik_entrypoints:
            self.traefik_entrypoints.append(change["new"])

    # FIXME: As above, can we enable TLS on only certain routers / entrypoints?
    traefik_tls = Bool(
        config=True, help="""Enable TLS on the jupyterhub-configured traefik routers."""
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.log_level:
            self._set_log_level()
        if self.default_entrypoint not in self.traefik_entrypoints:
            self.traefik_entrypoints.append(self.default_entrypoint)

    def _set_log_level(self):
        import sys, logging
        # Check we don't already have a StreamHandler
        # and add one if necessary
        addHandler = True
        for handler in self.log.handlers:
            if isinstance(handler, logging.StreamHandler):
                addHandler = False
        level = self.log_level
        if addHandler:
            self.log.setLevel(level)
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(level)
            self.log.addHandler(handler)

    @default("traefik_api_password")
    def _warn_empty_password(self):
        self.log.warning("Traefik API password was not set.")

        if self.should_start:
            # Generating tokens is fine if the Hub is starting the proxy
            self.log.warning("Generating a random token for traefik_api_username...")
            return new_token()

        self.log.warning(
            "Please set c.TraefikProxy.traefik_api_password to authenticate with traefik"
            " if the proxy was not started by the Hub."
        )
        return ""

    traefik_api_username = Unicode(
        config=True, help="""The username for traefik api login"""
    )

    @default("traefik_api_username")
    def _warn_empty_username(self):
        self.log.warning("Traefik API username was not set.")

        if self.should_start:
            self.log.warning('Defaulting traefik_api_username to "jupyterhub"')
            return "jupyterhub"

        self.log.warning(
            "Please set c.TraefikProxy.traefik_api_username to authenticate with traefik"
            " if the proxy was not started by the Hub."
        )
        return ""

    traefik_api_hashed_password = Unicode()

    check_route_timeout = Integer(
        30,
        config=True,
        help="""Timeout (in seconds) when waiting for traefik to register an updated route.""",
    )

    def _generate_htpassword(self):
        from passlib.hash import apr_md5_crypt
        self.traefik_api_hashed_password = apr_md5_crypt.hash(self.traefik_api_password)

    async def _check_for_traefik_service(self, routespec, kind):
        """Check for an expected router or service in the Traefik API.

        This is used to wait for traefik to load configuration
        from a provider
        """
        # expected e.g. 'service' + '_' + routespec @ file
        expected = traefik_utils.generate_alias(routespec, kind) + "@" + self.provider_name
        path = f"/api/http/{kind}s"
        try:
            resp = await self._traefik_api_request(path)
            json_data = json.loads(resp.body)
        except Exception:
            self.log.exception(f"Error checking traefik api for {kind} {routespec}")
            return False

        service_names = [service['name'] for service in json_data]
        if expected not in service_names:
            self.log.debug(f"traefik {expected} not yet in {kind}")
            return False

        # found the expected endpoint
        return True

    async def _wait_for_route(self, routespec):
        self.log.info(f"Waiting for {routespec} to register with traefik")

        async def _check_traefik_dynamic_conf_ready():
            """Check if traefik loaded its dynamic configuration yet"""
            if not await self._check_for_traefik_service(
                routespec, "service"
            ):
                return False
            if not await self._check_for_traefik_service(
                routespec, "router"
            ):
                return False

            return True

        await exponential_backoff(
            _check_traefik_dynamic_conf_ready,
            f"Traefik route for {routespec} configuration not available",
            timeout=self.check_route_timeout,
        )

    async def _traefik_api_request(self, path):
        """Make an API request to traefik"""
        url = url_path_join(self.traefik_api_url, path)
        self.log.debug("Fetching traefik api %s", url)
        resp = await AsyncHTTPClient().fetch(
            url,
            auth_username=self.traefik_api_username,
            auth_password=self.traefik_api_password,
            validate_cert=self.traefik_api_validate_cert,
        )
        if resp.code >= 300:
            self.log.warning("%s GET %s", resp.code, url)
        else:
            self.log.debug("%s GET %s", resp.code, url)

        self.log.debug(f"Succesfully received data from {path}: {resp.body}")
        return resp

    async def _wait_for_static_config(self):
        async def _check_traefik_static_conf_ready():
            """Check if traefik loaded its static configuration yet"""
            try:
                resp = await self._traefik_api_request("/api/overview")
            except Exception:
                self.log.exception("Error checking for traefik static configuration")
                return False

            if resp.code != 200:
                self.log.error(
                    "Unexpected response code %s checking for traefik static configuration",
                    resp.code,
                )
                return False

            return True

        await exponential_backoff(
            _check_traefik_static_conf_ready,
            "Traefik static configuration not available",
            timeout=self.check_route_timeout,
        )

    def _stop_traefik(self):
        self.log.info("Cleaning up proxy[%i]...", self.traefik_process.pid)
        self.traefik_process.terminate()
        try:
            self.traefik_process.communicate(timeout=10)
        except TimeoutExpired:
            self.traefik_process.kill()
            self.traefik_process.communicate()
        finally:
            self.traefik_process.wait()

    def _start_traefik(self):
        if self.provider_name not in ("file", "etcd", "consul"):
            raise ValueError(
                "Configuration mode not supported \n.\
                The proxy can only be configured through fileprovider, etcd and consul"
            )
        try:
            self.traefik_process = Popen([
                "traefik", "--configfile", abspath(self.static_config_file)
            ])
        except FileNotFoundError as e:
            self.log.error(
                "Failed to find traefik \n"
                "The proxy can be downloaded from https://github.com/containous/traefik/releases/download."
            )
            raise
        except Exception as e:
            self.log.exception(e)
            raise

    async def _setup_traefik_static_config(self):
        """When should_start=True, we are in control of traefik's static configuration
        file. This sets up the entrypoints and api handler in self.static_config, and
        then saves it to :attrib:`self.static_config_file`. 

        Subclasses should specify any traefik providers themselves, in
        :attrib:`self.static_config["providers"]` 
        """
        self.log.info("Setting up traefik's static config...")

        if self.traefik_log_level:
            self.static_config["log"] = { "level": self.traefik_log_level }

        entry_points = {}

        is_https = urlparse(self.public_url).scheme == "https"

        # FIXME: Do we only create a single entrypoint for jupyterhub?
        # Why not have an http and https entrypoint?
        if self.ssl_cert and self.ssl_key or is_https:
            entry_points[self.default_entrypoint] = {
                "address": ":" + str(urlparse(self.public_url).port),
                "tls": {},
            }
        else:
            entry_points[self.default_entrypoint] = {
                "address": ":" + str(urlparse(self.public_url).port)
            }

        entry_points["enter_api"] = {
            "address": ":" + str(urlparse(self.traefik_api_url).port),
        }
        self.static_config["entryPoints"] = entry_points
        self.static_config["api"] = {"dashboard": True} #, "entrypoints": "auth_api"}
        self.static_config["wss"] = {"protocol": "http"}

        try:
            self.log.debug(f"Persisting the static config: {self.static_config}")
            traefik_utils.persist_static_conf(
                self.static_config_file,
                self.static_config
            )
        except IOError:
            self.log.exception("Couldn't set up traefik's static config.")
            raise
        except:
            self.log.error("Couldn't set up traefik's static config. Unexpected error:")
            raise

    async def _setup_traefik_dynamic_config(self):
        self.log.info("Setting up traefik's dynamic config...")
        self._generate_htpassword()
        api_url = urlparse(self.traefik_api_url)
        api_path = api_url.path if api_url.path else '/api'
        api_credentials = "{0}:{1}".format(
            self.traefik_api_username,
            self.traefik_api_hashed_password
        )
        self.dynamic_config.update({
            "http": {
                "routers": {
                    "route_api": {
                        "rule": f"Host(`{api_url.hostname}`) && (PathPrefix(`{api_path}`) || PathPrefix(`/dashboard`))",
                        "entryPoints": ["enter_api"],
                        "service": "api@internal",
                        "middlewares": ["auth_api"]
                    },
                },
                "middlewares": {
                    "auth_api": {
                        "basicAuth": {
                            "users": [
                                api_credentials
                            ]
                        }
                    }
                }
            }
        })
        if self.ssl_cert and self.ssl_key:
            self.dynamic_config.update({
                "tls": {
                    "stores": {
                        "default": {
                            "defaultCertificate": {
                                "certFile": self.ssl_cert,
                                "keyFile": self.ssl_key
                            }
                        }
                    }
                }
            })

    def validate_routespec(self, routespec):
        """Override jupyterhub's default Proxy.validate_routespec method, as traefik
        can set router rule's on both Host and PathPrefix rules combined.
        """
        if not routespec.endswith("/"):
            routespec = routespec + "/"
        return routespec

    async def start(self):
        """Start the proxy.

        Will be called during startup if should_start is True.

        **Subclasses must define this method**
        if the proxy is to be started by the Hub
        """
        await self._setup_traefik_static_config()
        await self._setup_traefik_dynamic_config()
        self._start_traefik()

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

    async def persist_dynamic_config(self):
        """Update the Traefik dynamic configuration, depending on the backend
        provider in use. This is used to e.g. set up the api endpoint's
        authentication (username and password), as well as default tls
        certificates to use.

        :arg:`settings` is a Dict containing the traefik settings, which will
        be updated on the Traefik provider depending on the subclass in use.
        """
        raise NotImplementedError()
