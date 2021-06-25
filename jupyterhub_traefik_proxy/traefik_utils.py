import os
import string
from tempfile import NamedTemporaryFile
from traitlets import Unicode
from urllib.parse import unquote

import escapism

from contextlib import contextmanager
from collections import namedtuple


class KVStorePrefix(Unicode):
    def validate(self, obj, value):
        u = super().validate(obj, value)
        if u.endswith("/"):
            u = u.rstrip("/")

        proxy_class = type(obj).__name__
        if "Consul" in proxy_class and u.startswith("/"):
            u = u[1:]

        return u


def generate_rule(routespec):
    routespec = unquote(routespec)
    if routespec.startswith("/"):
        # Path-based route, e.g. /proxy/path/
        rule = f"PathPrefix(`{routespec}`)"
    else:
        # Host-based routing, e.g. host.tld/proxy/path/
        host, path_prefix = routespec.split("/", 1)
        rule = f"Host(`{host}`) && PathPrefix(`/{path_prefix}`)"
    return rule


def generate_alias(routespec, server_type=""):
    safe = string.ascii_letters + string.digits + "-"
    return server_type + "_" + escapism.escape(routespec, safe=safe)


def generate_service_entry( proxy, service_alias, separator="/", url=False):
    service_entry = separator.join(
        ["http", "services", service_alias, "loadBalancer", "servers", "server1"]
    )
    if separator == "/":
        service_entry = proxy.kv_traefik_prefix + separator + service_entry
    if url:
        service_entry += separator + "url"
    return service_entry


def generate_router_service_entry(proxy, router_alias):
    return "/".join(
        [proxy.kv_traefik_prefix, "http", "routers", router_alias, "service"]
    )
    #return proxy.kv_traefik_prefix + "routers/" + router_alias + "/service"


def generate_router_rule_entry(proxy, router_alias, separator="/"):
    router_rule_entry = separator.join(
        ["http", "routers", router_alias]
    )
    if separator == "/":
        router_rule_entry = separator.join(
            [proxy.kv_traefik_prefix, router_rule_entry, "rule"]
        )

    return router_rule_entry


def generate_route_keys(proxy, routespec, separator="/"):
    service_alias = generate_alias(routespec, "service")
    router_alias = generate_alias(routespec, "router")

    RouteKeys = namedtuple(
        "RouteKeys",
        [
            "service_alias",
            "service_url_path",
            "router_alias",
            "router_service_path",
            "router_rule_path",
        ],
    )

    if separator != ".":
        service_url_path = generate_service_entry(proxy, service_alias, url=True)
        router_rule_path = generate_router_rule_entry(proxy, router_alias)
        router_service_path = generate_router_service_entry(proxy, router_alias)
    else:
        service_url_path = generate_service_entry(
            proxy, service_alias, separator=separator
        )
        router_rule_path = generate_router_rule_entry(
            proxy, router_alias, separator=separator
        )
        router_service_path = ""

    return RouteKeys(
        service_alias,
        service_url_path,
        router_alias,
        router_service_path,
        router_rule_path,
    )


# atomic writing adapted from jupyter/notebook 5.7
# unlike atomic writing there, which writes the canonical path
# and only use the temp file for recovery,
# we write the temp file and then replace the canonical path
# to ensure that traefik never reads a partial file


@contextmanager
def atomic_writing(path):
    """Write temp file before copying it into place

    Avoids a partial file ever being present in `path`,
    which could cause traefik to load a partial routing table.
    """
    fileobj = NamedTemporaryFile(
        prefix=os.path.abspath(path) + "-tmp-", mode="w", delete=False
    )
    try:
        with fileobj as f:
            yield f
        os.replace(fileobj.name, path)
    finally:
        try:
            os.unlink(fileobj.name)
        except FileNotFoundError:
            # already deleted by os.replace above
            pass

class TraefikConfigFileHandler(object):
    """Handles reading and writing Traefik config files. Can operate
    on both toml and yaml files"""
    def __init__(self, file_path):
        file_ext = file_path.rsplit('.', 1)[-1]
        if file_ext == 'yaml':
            from ruamel.yaml import YAML
            config_handler = YAML(typ="safe")
        elif file_ext == 'toml':
            import toml as config_handler
        else:
            raise TypeError("type should be either 'toml' or 'yaml'")

        self.file_path = file_path
        # Redefined to either yaml.dump or toml.dump
        self._dump = config_handler.dump
        #self._dumps = config_handler.dumps
        # Redefined by __init__, to either yaml.load or toml.load
        self._load = config_handler.load

    def load(self):
        """Depending on self.file_path, call either yaml.load or toml.load"""
        with open(self.file_path, "r") as fd:
            return self._load(fd)

    def dump(self, data):
        with open(self.file_path, "w") as f:
            self._dump(data, f)

    def atomic_dump(self, data):
        """Save data to self.file_path after opening self.file_path with
        :func:`atomic_writing`"""
        with atomic_writing(self.file_path) as f:
            self._dump(data, f)

def persist_static_conf(file_path, static_conf_dict):
    handler = TraefikConfigFileHandler(file_path)
    handler.dump(static_conf_dict)

def persist_dynamic_conf(file_path, routes_dict):
    # FIXME: Only used by fileprovider, remove?
    handler = TraefikConfigFileHandler(file_path)
    handler.atomic_dump(routes_dict)

def load_dynamic_conf(file_path):
    # FIXME: Only used by fileprovider, remove?
    handler = TraefikConfigFileHandler(file_path)
    return handler.load()

# FIXME: Alias above functions for backwards compatibility?
persist_routes = persist_dynamic_conf
load_routes = load_dynamic_conf
