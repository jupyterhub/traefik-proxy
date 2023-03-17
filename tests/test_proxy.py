"""Tests for the treafik proxy implementations"""

import asyncio
import copy
import inspect
import pprint
import ssl
import subprocess
import sys
from contextlib import contextmanager
from os.path import abspath, dirname, join
from random import randint
from unittest.mock import Mock
from urllib.parse import quote, urlparse

import pytest
import utils
import websockets
from jupyterhub.objects import Hub, Server
from jupyterhub.user import User
from jupyterhub.utils import exponential_backoff, url_path_join
from tornado.httpclient import AsyncHTTPClient, HTTPClientError, HTTPRequest

from jupyterhub_traefik_proxy.proxy import TraefikProxy

# Mark all tests in this file as slow
pytestmark = [pytest.mark.slow]

pp = pprint.PrettyPrinter(indent=2)


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


def assert_equal(value, expected):
    try:
        assert value == expected
    except AssertionError:
        pp.pprint({'value': value})
        pp.pprint({"expected": expected})
        raise


@pytest.fixture(scope="session")
def launch_backends():
    """Launch n backends

    Session-scoped, so backends are re-used

    The fixture result is an async function that takes a number of backends required,
    and returns a list of URLs for those backends.

    When the function returns, the backends are already running and responsive.
    """

    dummy_server_path = abspath(join(dirname(__file__), "dummy_http_server.py"))
    running_backends = []
    urls = []
    base_port = 9000

    async def _launch_backends(n=1):
        """Launch `n` backends, returning their URLs

        Always returns a list of length `n`.
        """
        already_available = len(running_backends)
        for i in range(already_available, n):
            port = base_port + i
            url = f"http://127.0.0.1:{port}"
            print(f"Launching backend on {url}")
            backend = subprocess.Popen([sys.executable, dummy_server_path, str(port)])
            running_backends.append(backend)
            urls.append(url)

        if already_available < n:
            # await _new_ backends
            await wait_for_services(urls[already_available:])

        return urls[:n]

    yield _launch_backends

    for proc in running_backends:
        proc.terminate()
    for proc in running_backends:
        proc.communicate()
    for proc in running_backends:
        proc.wait()


async def wait_for_services(urls):
    # Wait until traefik and the backend are ready
    await exponential_backoff(
        utils.check_services_ready, "Service not reacheable", urls=urls
    )


def test_default_port():
    p = TraefikProxy(
        public_url="http://127.0.0.1/", traefik_api_url="https://127.0.0.1/"
    )
    assert p.public_url == "http://127.0.0.1:80/"
    assert p.traefik_api_url == "https://127.0.0.1:443/"

    with pytest.raises(ValueError):
        TraefikProxy(public_url="ftp://127.0.0.1:23/")


@pytest.mark.parametrize(
    "routespec, existing_routes",
    [
        # default route
        (
            "/",
            [
                "/abc",
                "/has%20space/",
                "/has%20space/foo/",
                "/missing-trailing/",
                "/missing-trailing/slash",
                "/has/",
                "/has/@/",
                "host.name/",
                "host.name/path/",
                "other.host/",
                "other.host/path/",
                "other.host/path/no/",
                "other.host/path/no/slash",
            ],
        ),
        ("/has%20space/foo/", ["/", "/has%20space/", "/has%20space/foo/abc/"]),
        (
            "/missing-trailing/slash",
            ["/", "/missing-trailing/", "/missing-trailing/slash/abc"],
        ),
        ("/has/@/", ["/", "/has/", "/has/@/abc/"]),
        (
            "/has/" + quote("üñîçø∂é"),
            ["/", "/has/", "/has/" + quote("üñîçø∂é") + "/abc/"],
        ),
        ("host.name/path/", ["/", "host.name/", "host.name/path/abc/"]),
        (
            "other.host/path/no/slash",
            [
                "/",
                "other.host/",
                "other.host/path/",
                "other.host/path/no/",
                "other.host/path/no/slash/abc/",
            ],
        ),
        (
            "/one/",
            [],
        ),
    ],
)
async def test_add_get_delete(
    request, proxy, launch_backends, routespec, existing_routes, event_loop
):
    data = {"test": "test1", "user": "username"}

    backends = await launch_backends(1 + len(existing_routes))

    default_backend = backends[0]
    extra_backends = backends[1:]

    proxy_url = proxy.public_url.rstrip("/")

    def normalize_spec(spec):
        return proxy.validate_routespec(spec)

    def expected_output(spec, url):
        return {
            "routespec": normalize_spec(spec),
            "target": url,
            "data": data,
        }

    # just use existing Jupyterhub check instead of making own one
    def expect_value_error(spec):
        try:
            normalize_spec(spec)
        except ValueError:
            return True

        return False

    @contextmanager
    def context(spec):
        if expect_value_error(spec):
            with pytest.raises(ValueError):
                yield
        else:
            yield

    async def test_route_exist(spec, backend):
        with context(spec):
            route = await proxy.get_route(spec)

        if not expect_value_error(spec):
            try:
                del route["data"]["last_activity"]  # CHP
            except TypeError as e:
                raise TypeError(f"{e}\nRoute got:{route}")
            except KeyError:
                pass

            assert_equal(route, expected_output(spec, backend))

            # Test the actual routing
            responding_backend1 = await utils.get_responding_backend_port(
                proxy_url, normalize_spec(spec)
            )
            responding_backend2 = await utils.get_responding_backend_port(
                proxy_url, normalize_spec(spec) + "something"
            )
            assert responding_backend1 == urlparse(backend).port
            assert responding_backend2 == urlparse(backend).port

    # Create existing routes
    futures = []
    for i, spec in enumerate(existing_routes):
        f = proxy.add_route(spec, extra_backends[i], copy.copy(data))
        futures.append(f)

    if futures:
        await asyncio.gather(*futures)

    def finalizer():
        async def cleanup():
            """Cleanup"""
            futures = []
            for spec in existing_routes:
                try:
                    f = proxy.delete_route(spec)
                    futures.append(f)
                except Exception:
                    pass
            if futures:
                await asyncio.gather(*futures)

        event_loop.run_until_complete(cleanup())

    request.addfinalizer(finalizer)

    # Test add
    with context(routespec):
        await proxy.add_route(routespec, default_backend, copy.copy(data))

    # Test get
    await test_route_exist(routespec, default_backend)
    for i, spec in enumerate(existing_routes):
        await test_route_exist(spec, extra_backends[i])

    # Test delete
    with context(routespec):
        await proxy.delete_route(routespec)
        route = await proxy.get_route(routespec)

    # Test that deleted route does not exist anymore
    if not expect_value_error(routespec):
        assert_equal(route, None)

        async def _wait_for_deletion():
            deleted = 0
            for spec in [
                normalize_spec(routespec),
                normalize_spec(routespec) + "something",
            ]:
                try:
                    result = await utils.get_responding_backend_port(proxy_url, spec)
                    if result != urlparse(default_backend).port:
                        deleted += 1
                except HTTPClientError:
                    deleted += 1

            return deleted == 2

        # If this raises a TimeoutError, the route wasn't properly deleted,
        # thus the proxy still has a route for the given routespec
        await exponential_backoff(_wait_for_deletion, "Route still exists")

    # Test that other routes are still exist
    for i, spec in enumerate(existing_routes):
        await test_route_exist(spec, extra_backends[i])


async def test_get_all_routes(proxy, launch_backends):
    # initial state: no routes
    routes = await proxy.get_all_routes()
    assert routes == {}

    routespecs = ["/proxy/path1", "/proxy/path2/", "/proxy/path3/"]
    targets = await launch_backends(len(routespecs))
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

    futures = []
    for routespec, target, data in zip(routespecs, targets, datas):
        f = proxy.add_route(routespec, target, copy.copy(data))
        futures.append(f)
    if futures:
        await asyncio.gather(*futures)

    routes = await proxy.get_all_routes()
    try:
        for route_key in routes.keys():
            del routes[route_key]["data"]["last_activity"]  # CHP
    except KeyError:
        pass

    assert_equal(routes, expected_output)

    for routespec in routespecs:
        await proxy.delete_route(routespec)
    routes = await proxy.get_all_routes()
    assert routes == {}


async def test_host_origin_headers(proxy, launch_backends):
    routespec = "/user/username/"
    target = "http://127.0.0.1:9000"
    data = {}

    proxy_url = urlparse(proxy.public_url)
    traefik_port = proxy_url.port
    traefik_host = proxy_url.hostname
    backends = await launch_backends(1)
    target = backends[0]
    urlparse(target).port

    # wait for traefik to be reachable
    await exponential_backoff(
        utils.check_host_up_http,
        "Traefik not reacheable",
        url=proxy_url.geturl(),
    )

    # wait for backend to be reachable
    await exponential_backoff(
        utils.check_host_up_http,
        "Backends not reacheable",
        url=target,
    )

    # Add route to default_backend
    await proxy.add_route(routespec, target, data)

    req_url = proxy.public_url.rstrip("/") + routespec

    expected_host_header = traefik_host + ":" + str(traefik_port)
    expected_origin_header = proxy.public_url + routespec

    req = HTTPRequest(
        req_url,
        method="GET",
        headers={"Host": expected_host_header, "Origin": expected_origin_header},
        validate_cert=False,
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
    f = spawner.start()
    if inspect.isawaitable(f):
        await f
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
    assert_equal(before, after)


async def test_websockets(proxy, launch_backends):
    routespec = "/user/username/"
    data = {}

    proxy_url = urlparse(proxy.public_url)
    proxy_url.port
    proxy_url.hostname
    backends = await launch_backends(1)
    target = backends[0]
    default_backend_port = urlparse(target).port

    # Add route to default_backend
    await proxy.add_route(routespec, target, data)

    if proxy.is_https:
        kwargs = {'ssl': ssl._create_unverified_context()}
        scheme = "wss://"
    else:
        kwargs = {}
        scheme = "ws://"
    req_url = scheme + proxy_url.netloc + url_path_join(routespec, "ws")

    # Don't validate the ssl certificate, it's self-signed by traefik
    print(f"Connecting with websockets to {req_url}")
    async with websockets.connect(req_url, **kwargs) as websocket:
        port = await websocket.recv()

    assert port == str(default_backend_port)
