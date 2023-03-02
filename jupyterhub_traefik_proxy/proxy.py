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
from os.path import abspath
from subprocess import Popen, TimeoutExpired
from urllib.parse import urlparse, urlunparse

from jupyterhub.proxy import Proxy
from jupyterhub.utils import exponential_backoff, new_token, url_path_join
from tornado.httpclient import AsyncHTTPClient, HTTPClientError
from traitlets import Any, Bool, Dict, Integer, Unicode, default, validate

from . import traefik_utils


class TraefikProxy(Proxy):
    """JupyterHub Proxy implementation using traefik"""

    traefik_process = Any()

    static_config_file = Unicode(
        "traefik.toml", config=True, help="""traefik's static configuration file"""
    )

    toml_static_config_file = Unicode(
        config=True,
        help="Deprecated. Use static_config_file",
    ).tag(
        deprecated_in="0.4",
        deprecated_for="static_config_file",
    )

    def _deprecated_trait(self, change):
        """observer for deprecated traits"""
        trait = change.owner.traits()[change.name]
        old_attr = change.name
        new_attr = trait.metadata["deprecated_for"]
        version = trait.metadata["deprecated_in"]
        if "." in new_attr:
            new_cls_attr = new_attr
            new_attr = new_attr.rsplit(".", 1)[1]
        else:
            new_cls_attr = f"{self.__class__.__name__}.{new_attr}"

        new_value = getattr(self, new_attr)
        if new_value != change.new:
            # only warn if different
            # protects backward-compatible config from warnings
            # if they set the same value under both names
            message = "{cls}.{old} is deprecated in {cls} {version}, use {new} instead".format(
                cls=self.__class__.__name__,
                old=old_attr,
                new=new_cls_attr,
                version=version,
            )
            self.log.warning(message)

            setattr(self, new_attr, change.new)

    def __init__(self, **kwargs):
        # observe deprecated config names in oauthenticator
        for name, trait in self.class_traits().items():
            if trait.metadata.get("deprecated_in"):
                self.observe(self._deprecated_trait, name)
        super().__init__(**kwargs)

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

    traefik_log_level = Unicode(config=True, help="""traefik's log level""")

    traefik_api_password = Unicode(
        config=True, help="""The password for traefik api login"""
    )

    traefik_env = Dict(
        config=True,
        help="""Environment variables to set for the traefik process.

        Only has an effect when traefik is a subprocess (should_start=True).
        """,
    )

    provider_name = Unicode(
        help="""The provider name that Traefik expects, e.g. file, consul, etcd"""
    )

    is_https = Bool(
        help="""Whether :attr:`.public_url` specifies an https entrypoint"""
    )

    @default("is_https")
    def get_is_https(self):
        # Check if we set https
        return urlparse(self.public_url).scheme == "https"

    @validate("public_url", "traefik_api_url")
    def _add_port(self, proposal):
        url = proposal.value
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(
                f"{self.__class__.__name__}.{proposal.trait.name} must be of the form http[s]://host:port/, got {url}"
            )
        if not parsed.port:
            # ensure port is defined
            if parsed.scheme == 'http':
                parsed = parsed._replace(netloc=f'{parsed.hostname}:80')
            elif parsed.scheme == 'https':
                parsed = parsed._replace(netloc=f'{parsed.hostname}:443')
            url = urlunparse(parsed)
        return url

    traefik_cert_resolver = Unicode(
        config=True,
        help="""The traefik certificate Resolver to use for requesting certificates""",
    )

    # FIXME: How best to enable TLS on routers assigned to only select
    # entrypoints defined here?
    traefik_entrypoint = Unicode(
        help="""The traefik entrypoint names, to which each """
        """jupyterhub-configred Traefik router is assigned"""
    )

    async def _get_traefik_entrypoint(self):
        """Find the traefik entrypoint that matches our :attrib:`self.public_url`"""
        if self.should_start:
            if self.is_https:
                return "websecure"
            else:
                return "web"
        import re

        resp = await self._traefik_api_request("/api/entrypoints")
        json_data = json.loads(resp.body)
        public_url = urlparse(self.public_url)

        # Traefik entrypoint format described at:-
        # https://doc.traefik.io/traefik/routing/entrypoints/#address
        entrypoint_re = re.compile('([^:]+)?:([0-9]+)/?(tcp|udp)?')
        for entrypoint in json_data:
            host, port, prot = entrypoint_re.match(entrypoint["address"]).groups()
            if int(port) == public_url.port:
                return entrypoint["name"]
        entrypoints = [entrypoint["address"] for entrypoint in json_data]
        raise ValueError(
            f"No traefik entrypoint ports ({entrypoints}) match public_url: {self.public_url}!"
        )

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
        expected = (
            traefik_utils.generate_alias(routespec, kind) + "@" + self.provider_name
        )
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
            if not await self._check_for_traefik_service(routespec, "service"):
                return False
            if not await self._check_for_traefik_service(routespec, "router"):
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
        return resp

    async def _wait_for_static_config(self):
        async def _check_traefik_static_conf_ready():
            """Check if traefik loaded its static configuration yet"""
            try:
                await self._traefik_api_request("/api/overview")
            except ConnectionRefusedError:
                self.log.debug(
                    f"Connection Refused waiting for traefik at {self.traefik_api_url}. It's probably starting up..."
                )
                return False
            except HTTPClientError as e:
                if e.code == 599:
                    self.log.debug(
                        f"Connection error waiting for traefik at {self.traefik_api_url}. It's probably starting up..."
                    )
                    return False
                if e.code == 404:
                    self.log.debug(
                        f"traefik api at {e.response.request.url} overview not ready yet"
                    )
                    return False
                # unexpected
                self.log.error(f"Error checking for traefik static configuration {e}")
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
        if self.provider_name not in {"file", "etcd", "consul"}:
            raise ValueError(
                "Configuration mode not supported \n.\
                The proxy can only be configured through fileprovider, etcd and consul"
            )

        env = os.environ.copy()
        env.update(self.traefik_env)
        try:
            self.traefik_process = Popen(
                ["traefik", "--configfile", abspath(self.static_config_file)],
                env=env,
            )
        except FileNotFoundError:
            self.log.error(
                "Failed to find traefik\n"
                "The proxy can be downloaded from https://github.com/traefik/traefik/releases/."
            )
            raise

    async def _setup_traefik_static_config(self):
        """When should_start=True, we are in control of traefik's static configuration
        file. This sets up the entrypoints and api handler in self.static_config, and
        then saves it to :attrib:`self.static_config_file`.

        Subclasses should specify any traefik providers themselves, in
        :attrib:`self.static_config["providers"]`
        """

        if self.traefik_log_level:
            self.static_config["log"] = {"level": self.traefik_log_level}

        # FIXME: Do we only create a single entrypoint for jupyterhub?
        # Why not have an http and https entrypoint?
        if not self.traefik_entrypoint:
            self.traefik_entrypoint = await self._get_traefik_entrypoint()

        entrypoints = {
            self.traefik_entrypoint: {
                "address": urlparse(self.public_url).netloc,
            },
            "enter_api": {
                "address": urlparse(self.traefik_api_url).netloc,
            },
        }

        self.static_config["entryPoints"] = entrypoints
        self.static_config["api"] = {}

        self.log.info(f"Writing traefik static config: {self.static_config}")

        try:
            handler = traefik_utils.TraefikConfigFileHandler(self.static_config_file)
            handler.atomic_dump(self.static_config)
        except Exception:
            self.log.error("Couldn't set up traefik's static config.")
            raise

    async def _setup_traefik_dynamic_config(self):
        self.log.info("Setting up traefik's dynamic config...")
        self._generate_htpassword()
        api_url = urlparse(self.traefik_api_url)
        api_path = api_url.path if api_url.path else '/api'
        api_credentials = (
            f"{self.traefik_api_username}:{self.traefik_api_hashed_password}"
        )
        self.dynamic_config.update(
            {
                "http": {
                    "routers": {
                        "route_api": {
                            "rule": f"Host(`{api_url.hostname}`) && PathPrefix(`{api_path}`)",
                            "entryPoints": ["enter_api"],
                            "service": "api@internal",
                            "middlewares": ["auth_api"],
                        },
                    },
                    "middlewares": {
                        "auth_api": {"basicAuth": {"users": [api_credentials]}}
                    },
                }
            }
        )
        if self.ssl_cert and self.ssl_key:
            self.dynamic_config.update(
                {
                    "tls": {
                        "stores": {
                            "default": {
                                "defaultCertificate": {
                                    "certFile": self.ssl_cert,
                                    "keyFile": self.ssl_key,
                                }
                            }
                        }
                    }
                }
            )

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
        await self._wait_for_static_config()

    async def stop(self):
        """Stop the proxy.

        Will be called during teardown if should_start is True.

        **Subclasses must define this method**
        if the proxy is to be started by the Hub
        """
        self._stop_traefik()
        self._cleanup()

    def _cleanup(self):
        """Cleanup after stop

        Extend if there's more to cleanup than the static config file
        """
        if self.should_start:
            try:
                os.remove(self.static_config_file)
            except Exception as e:
                self.log.error(
                    f"Failed to remove traefik config file {self.static_config_file}: {e}"
                )

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
        """Save the Traefik dynamic configuration, depending on the backend
        provider in use. This is used to e.g. set up the api endpoint's
        authentication (username and password), as well as default tls
        certificates to use, when should_start is True.
        """
        raise NotImplementedError()
