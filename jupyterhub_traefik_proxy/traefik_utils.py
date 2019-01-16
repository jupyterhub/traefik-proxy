import sys
import json
import re
import shutil
import io
import os
import escapism
import string
import toml

from urllib.parse import urlparse
from urllib.parse import unquote
from contextlib import contextmanager
from collections import namedtuple


def generate_rule(routespec):
    routespec = unquote(routespec)
    if routespec.startswith("/"):
        # Path-based route, e.g. /proxy/path/
        rule = "PathPrefix:" + routespec
    else:
        # Host-based routing, e.g. host.tld/proxy/path/
        host, path_prefix = routespec.split("/", 1)
        path_prefix = "/" + path_prefix
        rule = "Host:" + host + ";PathPrefix:" + path_prefix
    return rule


def generate_alias(routespec, server_type=""):
    safe = string.ascii_letters + string.digits + "_-"
    return server_type + "_" + escapism.escape(routespec, safe=safe)


def generate_backend_entry(
    proxy, backend_alias, separator="/", url=False, weight=False
):
    backend_entry = ""
    if separator is "/":
        backend_entry = proxy.etcd_traefik_prefix
    backend_entry += separator.join(["backends", backend_alias, "servers", "server1"])
    if url is True:
        backend_entry += separator + "url"
    elif weight is True:
        backend_entry += separator + "weight"

    return backend_entry


def generate_frontend_backend_entry(proxy, frontend_alias):
    return proxy.etcd_traefik_prefix + "frontends/" + frontend_alias + "/backend"


def generate_frontend_rule_entry(proxy, frontend_alias, separator="/"):
    frontend_rule_entry = separator.join(
        ["frontends", frontend_alias, "routes", "test"]
    )
    if separator == "/":
        frontend_rule_entry = (
            proxy.etcd_traefik_prefix + frontend_rule_entry + separator + "rule"
        )

    return frontend_rule_entry


def generate_route_keys(proxy, routespec, separator="/"):
    backend_alias = generate_alias(routespec, "backend")
    frontend_alias = generate_alias(routespec, "frontend")

    RouteKeys = namedtuple(
        "RouteKeys",
        [
            "backend_alias",
            "backend_url_path",
            "backend_weight_path",
            "frontend_alias",
            "frontend_backend_path",
            "frontend_rule_path",
        ],
    )

    if separator != ".":
        backend_url_path = generate_backend_entry(proxy, backend_alias, url=True)
        frontend_rule_path = generate_frontend_rule_entry(proxy, frontend_alias)
        backend_weight_path = generate_backend_entry(proxy, backend_alias, weight=True)
        frontend_backend_path = generate_frontend_backend_entry(proxy, frontend_alias)
    else:
        backend_url_path = generate_backend_entry(
            proxy, backend_alias, separator=separator
        )
        frontend_rule_path = generate_frontend_rule_entry(
            proxy, frontend_alias, separator=separator
        )
        backend_weight_path = ""
        frontend_backend_path = ""

    return RouteKeys(
        backend_alias,
        backend_url_path,
        backend_weight_path,
        frontend_alias,
        frontend_backend_path,
        frontend_rule_path,
    )


def path_to_intermediate(path):
    """Name of the intermediate file used in atomic writes.
    The .~ prefix will make Dropbox ignore the temporary file."""
    dirname, basename = os.path.split(path)
    return os.path.join(dirname, ".~" + basename)


@contextmanager
def atomic_writing(path):
    tmp_path = path_to_intermediate(path)
    shutil.copy2(path, tmp_path)
    fileobj = io.open(path, "w")

    try:
        yield fileobj
    except:
        # Failed! Move the backup file back to the real path to avoid corruption
        fileobj.close()
        os.replace(tmp_path, path)
        raise

    # Flush to disk
    fileobj.flush()
    os.fsync(fileobj.fileno())
    fileobj.close()

    # Written successfully, now remove the backup copy
    os.remove(tmp_path)


def persist_static_conf(file, static_conf_dict):
    with open(file, "w") as f:
        toml.dump(static_conf_dict, f)


def persist_routes(file, routes_dict):
    with atomic_writing(file) as config_fd:
        toml.dump(routes_dict, config_fd)


def load_routes(file):
    try:
        with open(file, "r") as config_fd:
            return toml.load(config_fd)
    except:
        raise
