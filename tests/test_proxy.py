"""Tests for the base traefik proxy"""

import pytest
import json
from os.path import abspath, dirname, join, pardir
import subprocess
import sys

# mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

etcdctl_path = abspath(
    join(dirname(__file__), pardir, "etcd-v3.3.9-linux-amd64/etcdctl")
)

jupyterhub_prefix = "/jupyterhub"
default_backend_weight = "1"

# TODO: remove proxy from the args and move functions to utils file


def assert_etcdctl_get(key, expected_rv):
    assert (
        subprocess.check_output([etcdctl_path, "get", key])
        .decode(sys.stdout.encoding)
        .strip()
        == expected_rv
    )


def assert_etcdctl_put(key, value, expected_rv):
    assert (
        subprocess.check_output([etcdctl_path, "put", key, value])
        .decode(sys.stdout.encoding)
        .strip()
        == expected_rv
    )


def add_route_with_etcdctl(proxy, routespec, target, data):
    expected_rv = "OK"
    jupyterhub_routespec = jupyterhub_prefix + routespec

    assert_etcdctl_put(jupyterhub_routespec, target, expected_rv)
    assert_etcdctl_put(target, json.dumps(data), expected_rv)

    backend_alias = proxy._create_backend_alias_from_url(target)
    backend_url_path = proxy._create_backend_url_path(backend_alias)
    assert_etcdctl_put(backend_url_path, target, expected_rv)

    backend_weight_path = proxy._create_backend_weight_path(backend_alias)
    assert_etcdctl_put(backend_weight_path, default_backend_weight, expected_rv)

    frontend_alias = proxy._create_frontend_alias_from_url(target)
    frontend_backend_path = proxy._create_frontend_backend_path(frontend_alias)
    assert_etcdctl_put(frontend_backend_path, backend_alias, expected_rv)

    # Test that a path-routing rule has been added for this frontend
    frontend_rule_path = proxy._create_frontend_rule_path(frontend_alias)
    if routespec.startswith("/"):
        # Path-based route, e.g. /proxy/path/
        rule = "PathPrefix:" + routespec
    else:
        # Host-based routing, e.g. host.tld/proxy/path/
        host, path_prefix = routespec.split("/", 1)
        path_prefix = "/" + path_prefix
        rule = "Host:" + host + ";PathPrefix:" + path_prefix
    assert_etcdctl_put(frontend_rule_path, rule, expected_rv)


def check_route_with_etcdl(proxy, routespec, target, data, test_deletion=False):
    jupyterhub_routespec = (
        jupyterhub_prefix + routespec
        if routespec.startswith("/")
        else jupyterhub_prefix + "/" + routespec
    )
    if test_deletion:
        expected_rv = ""
    else:
        expected_rv = jupyterhub_routespec + "\n" + target

    # Test that (routespec, target) pair has been added to etcd
    assert_etcdctl_get(jupyterhub_routespec, expected_rv)

    # Test that (target, data) pair has been added to etcd
    if not test_deletion:
        expected_rv = target + "\n" + json.dumps(data)
    assert_etcdctl_get(target, expected_rv)

    # Test that a backend has been added to etcd for this target
    backend_alias = proxy._create_backend_alias_from_url(target)
    backend_url_path = proxy._create_backend_url_path(backend_alias)
    if not test_deletion:
        expected_rv = backend_url_path + "\n" + target
    assert_etcdctl_get(backend_url_path, expected_rv)

    # Test that a backend weight has been added to etcd for this target
    backend_alias = proxy._create_backend_alias_from_url(target)
    backend_weight_path = proxy._create_backend_weight_path(backend_alias)
    if not test_deletion:
        expected_rv = backend_weight_path + "\n" + default_backend_weight
    assert_etcdctl_get(backend_weight_path, expected_rv)

    # Test that a frontend has been added for the prev backend
    frontend_alias = proxy._create_frontend_alias_from_url(target)
    frontend_backend_path = proxy._create_frontend_backend_path(frontend_alias)
    if not test_deletion:
        expected_rv = frontend_backend_path + "\n" + backend_alias
    assert_etcdctl_get(frontend_backend_path, expected_rv)

    # Test that a path-routing rule has been added for this frontend
    frontend_rule_path = proxy._create_frontend_rule_path(frontend_alias)

    if routespec.startswith("/"):
        # Path-based route, e.g. /proxy/path/
        rule = "PathPrefix:" + routespec
    else:
        # Host-based routing, e.g. host.tld/proxy/path/
        host, path_prefix = routespec.split("/", 1)
        path_prefix = "/" + path_prefix
        rule = "Host:" + host + ";PathPrefix:" + path_prefix

    if not test_deletion:
        expected_rv = frontend_rule_path + "\n" + rule
    assert_etcdctl_get(frontend_rule_path, expected_rv)


async def test_add_path_based_route_to_etcd(proxy):
    routespec = "/proxy/path"
    target = "http://127.0.0.1:99"
    data = {"test": "test1"}

    await proxy.add_route(routespec, target, data)

    try:
        check_route_with_etcdl(proxy, routespec, target, data)
    finally:
        await proxy.stop()


async def test_add_host_based_route_to_etcd(proxy):
    routespec = "host/proxy/path"
    target = "http://127.0.0.1:909"
    data = {"test": "test2"}

    await proxy.add_route(routespec, target, data)

    try:
        # Test that (routespec, target) pair has been added to etcd
        check_route_with_etcdl(proxy, routespec, target, data, False)
    finally:
        await proxy.stop()


async def test_delete_route_from_etcd(proxy):
    routespec = "/proxy/another_path"
    target = "http://127.0.0.1:990"
    data = {"test": "test3"}

    add_route_with_etcdctl(proxy, routespec, target, data)
    await proxy.delete_route("/proxy/another_path")
    try:
        # Test that (routespec, target) pair has been added to etcd
        check_route_with_etcdl(proxy, routespec, target, data, True)
    finally:
        await proxy.stop()


async def test_get_all_routes(proxy):
    # with pytest.raises(NotImplementedError):
    routes = await proxy.get_all_routes()
    print(json.dumps(routes, sort_keys=True, indent=4, separators=(",", ": ")))
    await proxy.stop()
    # TODO: test the routes


async def test_get_route(proxy):
    routespec = "/proxy/just_another_path"
    target = "http://127.0.0.1:990"
    data = {"test": "test4"}
    expected_output = {
        "routespec": routespec,
        "target": target,
        "data": json.dumps(data),
    }

    add_route_with_etcdctl(proxy, routespec, target, data)
    route = await proxy.get_route(routespec)

    assert route == expected_output
    await proxy.stop()
    # preety_formated_result = json.dumps(route, sort_keys=True, indent=4, separators=(",", ": "))
