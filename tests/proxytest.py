"""Tests for the base traefik proxy"""

import copy
import utils
import subprocess
import sys

from contextlib import contextmanager
from os.path import dirname, join, abspath
from random import randint
from unittest.mock import Mock
from urllib.parse import quote
from urllib.parse import urlparse

import pytest
from jupyterhub.objects import Hub, Server
from jupyterhub.user import User
from jupyterhub.utils import exponential_backoff, url_path_join
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPClientError
import websockets


class MockApp:
    def __init__(self):
        self.hub = Hub(routespec="/")


class MockSpawner:

    name = ""
    server = None
    pending = None

    def __init__(self, name="", *, user, **kwargs):
        self.name = name
        self.user = user
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.proxy_spec = url_path_join(self.user.proxy_spec, name, "/")

    def start(self):
        self.server = Server.from_url("http://127.0.0.1:%i" % randint(1025, 65535))

    def stop(self):
        self.server = None

    @property
    def ready(self):
        """Is this server ready to use?

        A server is not ready if an event is pending.
        """
        return self.server is not None

    @property
    def active(self):
        """Return True if the server is active.

        This includes fully running and ready or any pending start/stop event.
        """
        return self.ready


class MockUser(User):
    """Mock User for use in proxytest"""

    def __init__(self, name):
        orm_user = Mock()
        orm_user.name = name
        orm_user.orm_spawners = ""
        super().__init__(orm_user=orm_user, db=Mock())

    def _new_spawner(self, spawner_name, **kwargs):
        return MockSpawner(spawner_name, user=self, **kwargs)


@pytest.fixture
def launch_backend():
    dummy_server_path = abspath(join(dirname(__file__), "dummy_http_server.py"))
    running_backends = []

    def _launch_backend(port, proto="http"):
        backend = subprocess.Popen(
            [sys.executable, dummy_server_path, str(port), proto], stdout=None
        )
        running_backends.append(backend)

    yield _launch_backend

    for proc in running_backends:
        proc.kill()
    for proc in running_backends:
        proc.wait()


async def wait_for_services(urls):
    # Wait until traefik and the backend are ready
    await exponential_backoff(
        utils.check_services_ready, "Service not reacheable", urls=urls
    )


@pytest.mark.parametrize(
    "routespec",
    [
        "/",  # default route
        "/has%20space/foo/",
        "/missing-trailing/slash",
        "/has/@/",
        "/has/" + quote("üñîçø∂é"),
        "host.name/path/",
        "other.host/path/no/slash",
    ],
)
async def test_add_get_delete(proxy, launch_backend, routespec):
    target = "http://127.0.0.1:9000"
    data = {"test": "test1", "user": "username"}
    expected_output = {
        "routespec": routespec if routespec.endswith("/") else routespec + "/",
        "target": target,
        "data": data,
    }

    backend_port = urlparse(target).port
    launch_backend(backend_port)
    await wait_for_services([proxy.public_url, target])

    # host-routes when not host-routing raises an error
    # and vice versa
    subdomain_host = False
    try:
        subdomain_host = bool(proxy.app.subdomain_host)
    except AttributeError:
        pass
    finally:
        expect_value_error = subdomain_host ^ (not routespec.startswith("/"))

    @contextmanager
    def context():
        if expect_value_error:
            with pytest.raises(ValueError):
                yield
        else:
            yield

    """ Test add and get """
    with context():
        await proxy.add_route(routespec, target, copy.copy(data))
        # Make sure the route was added
        route = await proxy.get_route(routespec)
    if not expect_value_error:
        try:
            del route["data"]["last_activity"]  # CHP
        except KeyError:
            pass
        finally:
            assert route == expected_output
        if proxy.public_url.endswith("/"):
            req_url = proxy.public_url[:-1]
        else:
            req_url = proxy.public_url
        # Test the actual routing
        responding_backend1 = await utils.get_responding_backend_port(
            req_url, routespec
        )
        responding_backend2 = await utils.get_responding_backend_port(
            req_url, routespec + "/something"
        )
        assert (
            responding_backend1 == backend_port and responding_backend2 == backend_port
        )

    """ Test delete + get """
    with context():
        await proxy.delete_route(routespec)
        route = await proxy.get_route(routespec)
    if not expect_value_error:
        assert route == None

        async def _wait_for_deletion():
            deleted = False
            try:
                await utils.get_responding_backend_port(req_url, routespec)
            except HTTPClientError:
                deleted = True
            finally:
                return deleted

        """ If this raises a TimeoutError, the route wasn't properly deleted,
        thus the proxy still has a route for the given routespec"""
        await exponential_backoff(_wait_for_deletion, "Route still exists")


async def test_get_all_routes(proxy, launch_backend):
    routespecs = ["/proxy/path1", "/proxy/path2/", "/proxy/path3/"]
    targets = [
        "http://127.0.0.1:9900",
        "http://127.0.0.1:9090",
        "http://127.0.0.1:9999",
    ]
    datas = [{"test": "test1"}, {}, {"test": "test2"}]

    expected_output = {
        routespecs[0]
        + "/": {
            "routespec": routespecs[0] + "/",
            "target": targets[0],
            "data": datas[0],
        },
        routespecs[1]: {
            "routespec": routespecs[1],
            "target": targets[1],
            "data": datas[1],
        },
        routespecs[2]: {
            "routespec": routespecs[2],
            "target": targets[2],
            "data": datas[2],
        },
    }

    for target in targets:
        launch_backend(urlparse(target).port)

    await wait_for_services([proxy.public_url] + targets)

    for routespec, target, data in zip(routespecs, targets, datas):
        await proxy.add_route(routespec, target, copy.copy(data))

    routes = await proxy.get_all_routes()
    try:
        for route_key in routes.keys():
            del routes[route_key]["data"]["last_activity"]  # CHP
    except KeyError:
        pass
    finally:
        assert routes == expected_output


async def test_host_origin_headers(proxy, launch_backend):
    routespec = "/user/username/"
    target = "http://127.0.0.1:9000"
    data = {}

    traefik_port = urlparse(proxy.public_url).port
    traefik_host = urlparse(proxy.public_url).hostname
    default_backend_port = 9000
    launch_backend(default_backend_port)

    await exponential_backoff(
        utils.check_host_up, "Traefik not reacheable", ip="localhost", port=traefik_port
    )

    # Check if default backend is reacheable
    await exponential_backoff(
        utils.check_host_up,
        "Backends not reacheable",
        ip="localhost",
        port=default_backend_port,
    )
    # Add route to default_backend
    await proxy.add_route(routespec, target, data)

    if proxy.public_url.endswith("/"):
        req_url = proxy.public_url[:-1] + routespec
    else:
        req_url = proxy.public_url + routespec

    expected_host_header = traefik_host + ":" + str(traefik_port)
    expected_origin_header = proxy.public_url + routespec

    req = HTTPRequest(
        req_url,
        method="GET",
        headers={"Host": expected_host_header, "Origin": expected_origin_header},
    )
    resp = await AsyncHTTPClient().fetch(req)

    assert resp.headers["Host"] == expected_host_header
    assert resp.headers["Origin"] == expected_origin_header


@pytest.mark.parametrize("username", ["zoe", "50fia", "秀樹", "~TestJH", "has@"])
async def test_check_routes(proxy, username):
    # fill out necessary attributes for check_routes
    proxy.app = MockApp()
    proxy.hub = proxy.app.hub

    users = {}
    services = {}
    # run initial check first, to ensure that `/` is in the routes
    await proxy.check_routes(users, services)
    routes = await proxy.get_all_routes()
    assert sorted(routes) == ["/"]

    users[username] = test_user = MockUser(username)
    spawner = test_user.spawners[""]
    spawner.start()
    assert spawner.ready
    assert spawner.active
    await proxy.add_user(test_user, "")

    # check a valid route exists for user
    routes = await proxy.get_all_routes()
    before = sorted(routes)
    assert test_user.proxy_spec in before

    # check if a route is removed when user deleted
    await proxy.check_routes(users, services)
    await proxy.delete_user(test_user)
    routes = await proxy.get_all_routes()
    during = sorted(routes)
    assert test_user.proxy_spec not in during

    # check if a route exists for user
    await proxy.check_routes(users, services)
    routes = await proxy.get_all_routes()
    after = sorted(routes)
    assert test_user.proxy_spec in after

    # check that before and after state are the same
    assert before == after


async def test_websockets(proxy, launch_backend):
    routespec = "/user/username/"
    target = "http://127.0.0.1:9000"
    data = {}

    traefik_port = urlparse(proxy.public_url).port
    traefik_host = urlparse(proxy.public_url).hostname
    default_backend_port = 9000
    launch_backend(default_backend_port, "ws")

    await exponential_backoff(
        utils.check_host_up, "Traefik not reacheable", ip="localhost", port=traefik_port
    )

    # Check if default backend is reacheable
    await exponential_backoff(
        utils.check_host_up,
        "Backend not reacheable",
        ip="localhost",
        port=default_backend_port,
    )
    # Add route to default_backend
    await proxy.add_route(routespec, target, data)

    public_url = proxy.public_url
    if proxy.public_url.endswith("/"):
        public_url = proxy.public_url[:-1]

    req_url = "ws://" + urlparse(proxy.public_url).netloc + routespec

    async with websockets.connect(req_url) as websocket:
        port = await websocket.recv()

    assert port == str(default_backend_port)


async def test_autohttps(pebble, autohttps_toml_proxy, launch_backend):
    proxy = autohttps_toml_proxy

    routespec = "/autohttps"
    target = "http://127.0.0.1:9900"

    backend_port = 9900
    launch_backend(backend_port)

    await wait_for_services([proxy.public_url, target])

    await proxy.add_route(routespec, target, {})

    await utils.wait_for_certificate_aquisition(proxy.traefik_acme_storage)

    # Test the actual routing
    req = HTTPRequest(proxy.public_url + routespec, method="GET", validate_cert=False)
    resp = await AsyncHTTPClient().fetch(req)
    backend_response = int(resp.body.decode("utf-8"))

    # Test we were redirected to https
    # https://127.0.0.1:8443/autohttps
    expected_final_redirect_url = (
        "https://"
        + urlparse(proxy.public_url).hostname
        + ":"
        + str(proxy.traefik_https_port)
        + routespec
    )
    assert resp.effective_url == expected_final_redirect_url

    # Test redirection to the route added
    assert backend_response == backend_port
