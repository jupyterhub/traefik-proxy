"""Tests for the base traefik proxy"""

import pytest
import json
from os.path import abspath, dirname, join, pardir
import subprocess
import sys
from jupyterhub_traefik_proxy import traefik_utils
import asyncio

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

etcdctl_path = abspath(
    join(dirname(__file__), pardir, "etcd-v3.3.10-linux-amd64/etcdctl")
)

default_backend_weight = "1"


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


def assert_etcdctl_del(key, expected_rv):
    assert (
        subprocess.check_output([etcdctl_path, "del", key])
        .decode(sys.stdout.encoding)
        .strip()
        == expected_rv
    )


def cleanup_test_route(proxy, routespec, target, data):
    jupyterhub_routespec = proxy.etcd_jupyterhub_prefix + routespec
    backend_alias = traefik_utils.create_backend_alias_from_url(target)
    backend_url_path = traefik_utils.create_backend_url_path(proxy, backend_alias)
    backend_weight_path = traefik_utils.create_backend_weight_path(proxy, backend_alias)
    frontend_alias = traefik_utils.create_frontend_alias_from_url(target)
    frontend_backend_path = traefik_utils.create_frontend_backend_path(
        proxy, frontend_alias
    )
    frontend_rule_path = traefik_utils.create_frontend_rule_path(proxy, frontend_alias)
    expected_rv = "1"  # Number of deleted entries

    assert_etcdctl_del(jupyterhub_routespec, expected_rv)
    assert_etcdctl_del(target, expected_rv)
    assert_etcdctl_del(backend_url_path, expected_rv)
    assert_etcdctl_del(backend_weight_path, expected_rv)
    assert_etcdctl_del(frontend_backend_path, expected_rv)
    assert_etcdctl_del(frontend_rule_path, expected_rv)


def add_route_with_etcdctl(proxy, routespec, target, data):
    jupyterhub_routespec = proxy.etcd_jupyterhub_prefix + routespec
    backend_alias = traefik_utils.create_backend_alias_from_url(target)
    backend_url_path = traefik_utils.create_backend_url_path(proxy, backend_alias)
    backend_weight_path = traefik_utils.create_backend_weight_path(proxy, backend_alias)
    frontend_alias = traefik_utils.create_frontend_alias_from_url(target)
    frontend_backend_path = traefik_utils.create_frontend_backend_path(
        proxy, frontend_alias
    )
    frontend_rule_path = traefik_utils.create_frontend_rule_path(proxy, frontend_alias)
    if routespec.startswith("/"):
        # Path-based route, e.g. /proxy/path/
        rule = "PathPrefix:" + routespec
    else:
        # Host-based routing, e.g. host.tld/proxy/path/
        host, path_prefix = routespec.split("/", 1)
        path_prefix = "/" + path_prefix
        rule = "Host:" + host + ";PathPrefix:" + path_prefix
    expected_rv = "OK"

    assert_etcdctl_put(jupyterhub_routespec, target, expected_rv)
    assert_etcdctl_put(target, json.dumps(data), expected_rv)
    assert_etcdctl_put(backend_url_path, target, expected_rv)
    assert_etcdctl_put(backend_weight_path, default_backend_weight, expected_rv)
    assert_etcdctl_put(frontend_backend_path, backend_alias, expected_rv)
    assert_etcdctl_put(frontend_rule_path, rule, expected_rv)


def check_route_with_etcdctl(proxy, routespec, target, data, test_deletion=False):
    jupyterhub_routespec = proxy.etcd_jupyterhub_prefix + routespec
    backend_alias = traefik_utils.create_backend_alias_from_url(target)
    backend_url_path = traefik_utils.create_backend_url_path(proxy, backend_alias)
    backend_alias = traefik_utils.create_backend_alias_from_url(target)
    backend_weight_path = traefik_utils.create_backend_weight_path(proxy, backend_alias)
    frontend_alias = traefik_utils.create_frontend_alias_from_url(target)
    frontend_backend_path = traefik_utils.create_frontend_backend_path(
        proxy, frontend_alias
    )
    frontend_rule_path = traefik_utils.create_frontend_rule_path(proxy, frontend_alias)
    if routespec.startswith("/"):
        # Path-based route, e.g. /proxy/path/
        rule = "PathPrefix:" + routespec
    else:
        # Host-based routing, e.g. host.tld/proxy/path/
        host, path_prefix = routespec.split("/", 1)
        path_prefix = "/" + path_prefix
        rule = "Host:" + host + ";PathPrefix:" + path_prefix

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
    if not test_deletion:
        expected_rv = backend_url_path + "\n" + target
    assert_etcdctl_get(backend_url_path, expected_rv)

    # Test that a backend weight has been added to etcd for this target
    if not test_deletion:
        expected_rv = backend_weight_path + "\n" + default_backend_weight
    assert_etcdctl_get(backend_weight_path, expected_rv)

    # Test that a frontend has been added for the prev backend
    if not test_deletion:
        expected_rv = frontend_backend_path + "\n" + backend_alias
    assert_etcdctl_get(frontend_backend_path, expected_rv)

    # Test that a path-routing rule has been added for this frontend
    if not test_deletion:
        expected_rv = frontend_rule_path + "\n" + rule
    assert_etcdctl_get(frontend_rule_path, expected_rv)


@pytest.mark.parametrize(
    "routespec, target, data",
    [
        ("/proxy/path", "http://127.0.0.1:99", {"test": "test1"}),  # Path-based routing
        ("/proxy/path", "http://127.0.0.1:99", {}),  # Path-based routing, no data dict
        # Host-based routing
        ("host/proxy/path", "http://127.0.0.1:99", {"test": "test2"}),
    ],
)
async def test_add_route_to_etcd(proxy, routespec, target, data):
    await proxy.add_route(routespec, target, data)

    try:
        check_route_with_etcdctl(proxy, routespec, target, data)
        cleanup_test_route(proxy, routespec, target, data)
    finally:
        await proxy.stop()


@pytest.mark.parametrize(
    "routespec, target, data",
    [
        ("/proxy/path", "http://127.0.0.1:99", {"test": "test1"}),  # Path-based routing
        ("/proxy/path", "http://127.0.0.1:99", {}),  # Path-based routing, no data dict
        # Host-based routing
        ("host/proxy/path", "http://127.0.0.1:99", {"test": "test2"}),
    ],
)
async def test_delete_route_from_etcd(proxy, routespec, target, data):
    add_route_with_etcdctl(proxy, routespec, target, data)
    await proxy.delete_route(routespec)

    try:
        # Test that (routespec, target) pair has been added to etcd
        check_route_with_etcdctl(proxy, routespec, target, data, True)
    finally:
        await proxy.stop()


@pytest.mark.parametrize(
    "routespec, target, data, expected_output",
    [
        (
            "/proxy/path",
            "http://127.0.0.1:99",
            {"test": "test1"},
            {
                "routespec": "/proxy/path",
                "target": "http://127.0.0.1:99",
                "data": json.dumps({"test": "test1"}),
            },
        ),  # Path-based routing
        (
            "/proxy/path",
            "http://127.0.0.1:99",
            {},
            {"routespec": "/proxy/path", "target": "http://127.0.0.1:99", "data": "{}"},
        ),  # Path-based routing, no data dict
        (
            "host/proxy/path",
            "http://127.0.0.1:99",
            {"test": "test2"},
            {
                "routespec": "host/proxy/path",
                "target": "http://127.0.0.1:99",
                "data": json.dumps({"test": "test2"}),
            },
        ),  # Host-based routing
    ],
)
async def test_get_route(proxy, routespec, target, data, expected_output):
    add_route_with_etcdctl(proxy, routespec, target, data)
    route = await proxy.get_route(routespec)
    cleanup_test_route(proxy, routespec, target, data)

    assert route == expected_output
    await proxy.stop()


async def test_get_all_routes(proxy):
    routespec = ["/proxy/path1", "/proxy/path2", "host/proxy/path"]
    target = ["http://127.0.0.1:990", "http://127.0.0.1:909", "http://127.0.0.1:999"]
    data = [{"test": "test1"}, {}, {"test": "test2"}]
    dict_keys = ["routespec", "target", "data"]

    expected_output = {
        routespec[0]: {
            "routespec": routespec[0],
            "target": target[0],
            "data": json.dumps(data[0]),
        },
        routespec[1]: {
            "routespec": routespec[1],
            "target": target[1],
            "data": json.dumps(data[1]),
        },
        routespec[2]: {
            "routespec": routespec[2],
            "target": target[2],
            "data": json.dumps(data[2]),
        },
    }

    add_route_with_etcdctl(proxy, routespec[0], target[0], data[0])
    add_route_with_etcdctl(proxy, routespec[1], target[1], data[1])
    add_route_with_etcdctl(proxy, routespec[2], target[2], data[2])
    routes = await proxy.get_all_routes()
    try:
        assert routes == expected_output
    finally:
        cleanup_test_route(proxy, routespec[0], target[0], data[0])
        cleanup_test_route(proxy, routespec[1], target[1], data[1])
        cleanup_test_route(proxy, routespec[2], target[2], data[2])
        await proxy.stop()


async def test_etcd_routing(proxy):
    routespec = ["/", "/user/first", "/user/second"]
    target = ["http://127.0.0.1:9000", "http://127.0.0.1:9090", "http://127.0.0.1:9099"]
    data = [{}, {}, {}]
    try:
        await proxy.add_route(routespec[0], target[0], data[0])
        await proxy.add_route(routespec[1], target[1], data[1])
        await proxy.add_route(routespec[2], target[2], data[2])
        """ Force the proxy reload its configuration from etcd, otherwise
            we have no other way to ensure traefik loaded the newly added routes
            from etcd.
        """
        proxy._stop_traefik()
        proxy._start_traefik()
        traefik_utils.check_traefik_up()
        traefik_utils.check_traefik_etcd_conf_ready()
        default_backend, first_backend, second_backend = traefik_utils.launch_backends()
        traefik_utils.check_backends_up()
        traefik_utils.check_routing()
    finally:
        default_backend.kill()
        first_backend.kill()
        second_backend.kill()
        default_backend.wait()
        first_backend.wait()
        second_backend.wait()
        await proxy.stop()
        cleanup_test_route(proxy, routespec[0], target[0], data[0])
        cleanup_test_route(proxy, routespec[1], target[1], data[1])
        cleanup_test_route(proxy, routespec[2], target[2], data[2])
