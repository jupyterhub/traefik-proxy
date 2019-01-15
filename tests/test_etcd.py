import asyncio
import pytest
import json
import subprocess
import sys
import utils
from jupyterhub_traefik_proxy import traefik_utils

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

default_backend_weight = "1"


def assert_etcdctl_get(key, expected_rv):
    assert (
        subprocess.check_output(["etcdctl", "get", key])
        .decode(sys.stdout.encoding)
        .strip()
        == expected_rv
    )


def assert_etcdctl_put(key, value, expected_rv):
    assert (
        subprocess.check_output(["etcdctl", "put", key, value])
        .decode(sys.stdout.encoding)
        .strip()
        == expected_rv
    )


def assert_etcdctl_del(key, expected_rv):
    assert (
        subprocess.check_output(["etcdctl", "del", key])
        .decode(sys.stdout.encoding)
        .strip()
        == expected_rv
    )


def add_route_with_etcdctl(etcd_proxy, routespec, target, data):
    proxy = etcd_proxy
    jupyterhub_routespec = proxy.etcd_jupyterhub_prefix + routespec
    route_keys = traefik_utils.generate_route_keys(proxy, routespec, routespec)
    rule = traefik_utils.generate_rule(routespec)
    expected_rv = "OK"

    assert_etcdctl_put(jupyterhub_routespec, target, expected_rv)
    assert_etcdctl_put(target, json.dumps(data), expected_rv)
    assert_etcdctl_put(route_keys.backend_url_path, target, expected_rv)
    assert_etcdctl_put(
        route_keys.backend_weight_path, default_backend_weight, expected_rv
    )
    assert_etcdctl_put(
        route_keys.frontend_backend_path, route_keys.backend_alias, expected_rv
    )
    assert_etcdctl_put(route_keys.frontend_rule_path, rule, expected_rv)


def check_route_with_etcdctl(etcd_proxy, routespec, target, data, test_deletion=False):
    proxy = etcd_proxy
    jupyterhub_routespec = proxy.etcd_jupyterhub_prefix + routespec
    route_keys = traefik_utils.generate_route_keys(proxy, routespec, routespec)
    rule = traefik_utils.generate_rule(routespec)

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
        expected_rv = route_keys.backend_url_path + "\n" + target
    assert_etcdctl_get(route_keys.backend_url_path, expected_rv)

    # Test that a backend weight has been added to etcd for this target
    if not test_deletion:
        expected_rv = route_keys.backend_weight_path + "\n" + default_backend_weight
    assert_etcdctl_get(route_keys.backend_weight_path, expected_rv)

    # Test that a frontend has been added for the prev backend
    if not test_deletion:
        expected_rv = route_keys.frontend_backend_path + "\n" + route_keys.backend_alias
    assert_etcdctl_get(route_keys.frontend_backend_path, expected_rv)

    # Test that a path-routing rule has been added for this frontend
    if not test_deletion:
        expected_rv = route_keys.frontend_rule_path + "\n" + rule
    assert_etcdctl_get(route_keys.frontend_rule_path, expected_rv)


@pytest.mark.parametrize("routespec", ["/proxy/path", "host/proxy/path"])
@pytest.mark.parametrize("target", ["http://127.0.0.1:99"])
@pytest.mark.parametrize("data", [{"test": "test1"}, {}])
async def test_add_route_to_etcd(etcd_proxy, routespec, target, data):
    proxy = etcd_proxy
    await proxy.add_route(routespec, target, data)
    check_route_with_etcdctl(proxy, routespec, target, data)


@pytest.mark.parametrize("routespec", ["/proxy/path", "host/proxy/path"])
@pytest.mark.parametrize("target", ["http://127.0.0.1:99"])
@pytest.mark.parametrize("data", [{"test": "test1"}, {}])
async def test_delete_route_from_etcd(etcd_proxy, routespec, target, data):
    proxy = etcd_proxy
    add_route_with_etcdctl(proxy, routespec, target, data)
    await proxy.delete_route(routespec)

    # Test that (routespec, target) pair has been deleted from etcd
    check_route_with_etcdctl(proxy, routespec, target, data, test_deletion=True)


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
async def test_get_route(etcd_proxy, routespec, target, data, expected_output):
    proxy = etcd_proxy
    add_route_with_etcdctl(proxy, routespec, target, data)
    route = await proxy.get_route(routespec)
    assert route == expected_output


async def test_get_all_routes(etcd_proxy):
    proxy = etcd_proxy
    routespec = ["/proxy/path1", "/proxy/path2", "host/proxy/path"]
    target = ["http://127.0.0.1:990", "http://127.0.0.1:909", "http://127.0.0.1:999"]
    data = [{"test": "test1"}, {}, {"test": "test2"}]

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
    assert routes == expected_output
