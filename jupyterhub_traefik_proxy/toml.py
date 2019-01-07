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
from functools import wraps

from urllib.parse import urlparse
from traitlets import Any, default, Unicode

from . import traefik_utils
from jupyterhub.proxy import Proxy
from jupyterhub.utils import exponential_backoff


class TraefikTomlProxy(Proxy):
    """JupyterHub Proxy implementation using traefik and toml config file"""

    traefik_process = Any()

    toml_static_config_file = Unicode(
        "traefik.toml", config=True, help="""traefik's configuration file"""
    )

    toml_dynamic_config_file = Unicode(
        "rules.toml", config=True, help="""traefik's configuration file"""
    )

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

    mutex = asyncio.Lock()

    routes_cache = {}

    async def _wait_for_route(self, target):
        await exponential_backoff(
            traefik_utils.check_traefik_dynamic_conf_ready,
            "Traefik route for %s configuration not available" % target,
            username=self.traefik_api_username,
            password=self.traefik_api_password,
            timeout=20,
            api_url=self.traefik_api_url,
            target=target,
            provider="file"
        )

    async def _wait_for_static_config(self):
        await exponential_backoff(
            traefik_utils.check_traefik_static_conf_ready,
            "Traefik static configuration not available",
            username=self.traefik_api_username,
            password=self.traefik_api_password,
            timeout=20,
            api_url=self.traefik_api_url,
            provider="file"
        )

    async def _setup_traefik_static_config(self):
        self.log.info("Setting up traefik's static config...")
        self._create_htpassword()

        with open(self.toml_static_config_file, "w") as f:
            f.write('defaultEntryPoints = ["http"]\n')
            f.write("debug = true\n"),
            f.write('logLevel = "ERROR"\n')

            f.write("[entryPoints]\n"),
            f.write("\t[entryPoints.http]\n")
            f.write('\t\taddress = ":' + str(urlparse(self.public_url).port) + '"\n')
            f.write("\t[entryPoints.auth_api]\n")
            f.write(
                '\t\taddress = ":' + str(urlparse(self.traefik_api_url).port) + '"\n'
            )
            f.write("\t\t[entryPoints.auth_api.auth]\n")
            f.write("\t\t\t[entryPoints.auth_api.auth.basic]\n")
            f.write(
                '\t\t\t\tusers = ["'
                + self.traefik_api_username
                + ":"
                + self.traefik_api_hashed_password
                + '"]\n'
            )

            f.write("[api]\n"),
            f.write("\tdashboard = true\n"),
            f.write('\tentrypoint = "auth_api"\n'),

            f.write("[file]\n")
            f.write('\tfilename = "' + self.toml_dynamic_config_file + '"\n')
            f.write("\twatch = true\n")
        open(self.toml_dynamic_config_file, "a").close()

    def _start_traefik(self):
        self.log.info("Starting traefik...")
        try:
            self.traefik_process = traefik_utils.launch_traefik_with_toml()
        except FileNotFoundError as e:
            self.log.error(
                "Failed to find traefik \n"
                "The proxy can be downloaded from https://github.com/containous/traefik/releases/download."
            )
            raise

    def _stop_traefik(self):
        self.log.info("Cleaning up proxy[%i]...", self.traefik_process.pid)
        self.traefik_process.kill()
        self.traefik_process.wait()

    def _cleanup_config_files(self):
        try:
            os.remove(self.toml_static_config_file)
            os.remove(self.toml_dynamic_config_file)
        except:
            self.log.error("Failed to remove traefik's configuration files \n")
            raise

    def _get_route_unsafe(self, routespec):
        result = {
            "routespec": routespec,
            "target": self.routes_cache[routespec]["target"],
            "data": self.routes_cache[routespec]["data"],
        }
        return result

    def _create_htpassword(self):
        from passlib.apache import HtpasswdFile

        ht = HtpasswdFile()
        ht.set_password(self.traefik_api_username, self.traefik_api_password)
        self.traefik_api_hashed_password = str(ht.to_string()).split(":")[1][:-3]

    def _persist_routes(self, config_fd):
        config_fd.write("[frontends]\n")
        for key, value in self.routes_cache.items():
            config_fd.write("".join(value["frontend"]))
        config_fd.write("[backends]\n")
        for key, value in self.routes_cache.items():
            config_fd.write("".join(value["backend"]))

    def _update_config_file(self):
        tmp = open("tmp.toml", "w")
        self._persist_routes(tmp)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp.close()
        try:
            os.rename("tmp.toml", self.toml_dynamic_config_file)
        except Exception as e:
            self.log.error("Failed to update traefik's dynamic configuration file")

    async def start(self):
        """Start the proxy.

        Will be called during startup if should_start is True.

        **Subclasses must define this method**
        if the proxy is to be started by the Hub
        """
        self._start_traefik()
        await self._setup_traefik_static_config()
        await self._wait_for_static_config()


    async def stop(self):
        """Stop the proxy.

        Will be called during teardown if should_start is True.

        **Subclasses must define this method**
        if the proxy is to be started by the Hub
        """
        self._stop_traefik()
        self._cleanup_config_files()

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

        backend_alias = traefik_utils.create_alias(target, "backend")
        backend_url_path = traefik_utils.create_backend_entry(
            self, backend_alias, separator="."
        )
        frontend_alias = traefik_utils.create_alias(target, "frontend")
        frontend_rule_path = traefik_utils.create_frontend_rule_entry(
            self, frontend_alias, separator="."
        )
        data = json.dumps(data)

        if routespec.startswith("/"):
            # Path-based route, e.g. /proxy/path/
            rule = "PathPrefix:" + routespec
        else:
            # Host-based routing, e.g. host.tld/proxy/path/
            host, path_prefix = routespec.split("/", 1)
            path_prefix = "/" + path_prefix
            rule = "Host:" + host + ";PathPrefix:" + path_prefix

        await self.mutex.acquire()
        try:
            self.routes_cache[routespec] = {
                "backend": [
                    "\t[backends." + backend_alias + "]\n",
                    "\t\t[" + backend_url_path + "]\n",
                    "\t\t\turl = " + '"' + target + '"\n',
                    "\t\t\tweight = " + "1\n",
                ],
                "frontend": [
                    "\t[frontends." + frontend_alias + "]\n",
                    "\t\tbackend = " + '"' + backend_alias + '"\n',
                    "\t\t[" + frontend_rule_path.rsplit(".", 1)[0] + "]\n",
                    "\t\t\trule = " + '"' + rule + '"\n',
                ],
                "data": data,
                "target": target,
            }
            self._update_config_file()
        finally:
            self.mutex.release()

        try:
            # Check if traefik was launched
            pid = self.traefik_process.pid
            await self._wait_for_route(target)
        except AttributeError:
            self.log.error(
                "You cannot add routes if the proxy isn't running! Please start the proxy: proxy.start()"
            )
            raise

    async def delete_route(self, routespec):
        """Delete a route with a given routespec if it exists.

        **Subclasses must define this method**
        """
        await self.mutex.acquire()
        try:
            del self.routes_cache[routespec]
            self._update_config_file()
        finally:
            self.mutex.release()

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

        Resuper.turns:
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
