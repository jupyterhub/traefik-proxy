import asyncio
import pytest
import json
import subprocess
import sys
import utils
from jupyterhub_traefik_proxy import traefik_utils
from urllib.parse import quote

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

default_backend_weight = "1"


def assert_etcdctl_get(key, expected_rv, user, password):
    command = ["etcdctl", "get", key]
    if user and password:
        command = ["etcdctl", "--user", user + ":" + password, "get", key]
    assert (
        subprocess.check_output(command).decode(sys.stdout.encoding).strip()
        == expected_rv
    )


def assert_etcdctl_put(key, value, expected_rv, user, password):
    command = ["etcdctl", "put", key, value]
    if user and password:
        command = ["etcdctl", "--user", user + ":" + password, "put", key, value]
    assert (
        subprocess.check_output(command).decode(sys.stdout.encoding).strip()
        == expected_rv
    )


def add_route_with_etcdctl(etcd_proxy, routespec, target, data, user="", password=""):
    proxy = etcd_proxy

    if not routespec.endswith("/"):
        routespec = routespec + "/"

    jupyterhub_routespec = proxy.etcd_jupyterhub_prefix + routespec
    route_keys = traefik_utils.generate_route_keys(proxy, routespec)
    rule = traefik_utils.generate_rule(routespec)
    expected_rv = "OK"

    assert_etcdctl_put(jupyterhub_routespec, target, expected_rv, user, password)
    assert_etcdctl_put(target, json.dumps(data), expected_rv, user, password)
    assert_etcdctl_put(route_keys.backend_url_path, target, expected_rv, user, password)
    assert_etcdctl_put(
        route_keys.backend_weight_path,
        default_backend_weight,
        expected_rv,
        user,
        password,
    )
    assert_etcdctl_put(
        route_keys.frontend_backend_path,
        route_keys.backend_alias,
        expected_rv,
        user,
        password,
    )
    assert_etcdctl_put(route_keys.frontend_rule_path, rule, expected_rv, user, password)


def check_route_with_etcdctl(
    etcd_proxy, routespec, target, data, user="", password="", test_deletion=False
):
    proxy = etcd_proxy

    if not routespec.endswith("/"):
        routespec = routespec + "/"

    jupyterhub_routespec = proxy.etcd_jupyterhub_prefix + routespec
    route_keys = traefik_utils.generate_route_keys(proxy, routespec)
    rule = traefik_utils.generate_rule(routespec)

    if test_deletion:
        expected_rv = ""
    else:
        expected_rv = jupyterhub_routespec + "\n" + target

    # Test that (routespec, target) pair has been added to etcd
    assert_etcdctl_get(jupyterhub_routespec, expected_rv, user, password)

    # Test that (target, data) pair has been added to etcd
    if not test_deletion:
        expected_rv = target + "\n" + json.dumps(data)
    assert_etcdctl_get(target, expected_rv, user, password)

    # Test that a backend has been added to etcd for this target
    if not test_deletion:
        expected_rv = route_keys.backend_url_path + "\n" + target
    assert_etcdctl_get(route_keys.backend_url_path, expected_rv, user, password)

    # Test that a backend weight has been added to etcd for this target
    if not test_deletion:
        expected_rv = route_keys.backend_weight_path + "\n" + default_backend_weight
    assert_etcdctl_get(route_keys.backend_weight_path, expected_rv, user, password)

    # Test that a frontend has been added for the prev backend
    if not test_deletion:
        expected_rv = route_keys.frontend_backend_path + "\n" + route_keys.backend_alias
    assert_etcdctl_get(route_keys.frontend_backend_path, expected_rv, user, password)

    # Test that a path-routing rule has been added for this frontend
    if not test_deletion:
        expected_rv = route_keys.frontend_rule_path + "\n" + rule
    assert_etcdctl_get(route_keys.frontend_rule_path, expected_rv, user, password)


@pytest.mark.parametrize(
    "routespec",
    [
        "/has%20space/foo/",
        "/missing-trailing/slash",
        "/has/@/",
        "/has/" + quote("üñîçø∂é"),
        "host.name/path/",
        "other.host/path/no/slash",
    ],
)
async def test_add_route_to_etcd(etcd_proxy, routespec):
    proxy = etcd_proxy
    if not routespec.startswith("/"):
        proxy.host_routing = True

    target = "http://127.0.0.1:9000"
    data = {"test": "test1", "user": "username"}

    await proxy.add_route(routespec, target, data)

    if proxy.kv_password:
        check_route_with_etcdctl(
            proxy, routespec, target, data, proxy.kv_username, proxy.kv_password
        )
    else:
        check_route_with_etcdctl(proxy, routespec, target, data)


@pytest.mark.parametrize(
    "routespec",
    [
        "/has%20space/foo/",
        "/missing-trailing/slash",
        "/has/@/",
        "/has/" + quote("üñîçø∂é"),
        "host.name/path/",
        "other.host/path/no/slash",
    ],
)
async def test_delete_route_from_etcd(etcd_proxy, routespec):
    proxy = etcd_proxy
    if not routespec.startswith("/"):
        proxy.host_routing = True

    target = "http://127.0.0.1:9000"
    data = {"test": "test1", "user": "username"}

    if proxy.kv_password:
        add_route_with_etcdctl(
            proxy, routespec, target, data, proxy.kv_username, proxy.kv_password
        )
    else:
        add_route_with_etcdctl(proxy, routespec, target, data)

    await proxy.delete_route(routespec)

    # Test that (routespec, target) pair has been deleted from etcd
    if proxy.kv_password:
        check_route_with_etcdctl(
            proxy,
            routespec,
            target,
            data,
            proxy.kv_username,
            proxy.kv_password,
            test_deletion=True,
        )
    else:
        check_route_with_etcdctl(proxy, routespec, target, data, test_deletion=True)


@pytest.mark.parametrize(
    "routespec",
    [
        "/has%20space/foo/",
        "/missing-trailing/slash",
        "/has/@/",
        "/has/" + quote("üñîçø∂é"),
        "host.name/path/",
        "other.host/path/no/slash",
    ],
)
async def test_get_route(etcd_proxy, routespec):
    proxy = etcd_proxy
    if not routespec.startswith("/"):
        proxy.host_routing = True

    target = "http://127.0.0.1:9000"
    data = {"test": "test1", "user": "username"}

    expected_output = {
        "routespec": routespec if routespec.endswith("/") else routespec + "/",
        "target": target,
        "data": data,
    }

    if proxy.kv_password:
        add_route_with_etcdctl(
            proxy, routespec, target, data, proxy.kv_username, proxy.kv_password
        )
    else:
        add_route_with_etcdctl(proxy, routespec, target, data)

    route = await proxy.get_route(routespec)
    assert route == expected_output


async def test_get_all_routes(etcd_proxy):
    proxy = etcd_proxy
    routespec = ["/proxy/path1", "/proxy/path2/", "host/proxy/path"]
    target = ["http://127.0.0.1:990", "http://127.0.0.1:909", "http://127.0.0.1:999"]
    data = [{"test": "test1"}, {}, {"test": "test2"}]

    expected_output = {
        routespec[0]
        + "/": {"routespec": routespec[0] + "/", "target": target[0], "data": data[0]},
        routespec[1]: {"routespec": routespec[1], "target": target[1], "data": data[1]},
        routespec[2]
        + "/": {"routespec": routespec[2] + "/", "target": target[2], "data": data[2]},
    }

    user = ""
    password = ""

    if proxy.kv_password:
        user = proxy.kv_username
        password = proxy.kv_password

    add_route_with_etcdctl(proxy, routespec[0], target[0], data[0], user, password)
    add_route_with_etcdctl(proxy, routespec[1], target[1], data[1], user, password)
    add_route_with_etcdctl(proxy, routespec[2], target[2], data[2], user, password)
    routes = await proxy.get_all_routes()
    assert routes == expected_output
