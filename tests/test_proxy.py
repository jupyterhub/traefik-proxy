"""Tests for the base traefik proxy"""

import pytest
import utils
import websockets
import copy

from jupyterhub.utils import exponential_backoff
from contextlib import contextmanager
from urllib.parse import urlparse
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPClientError
from urllib.parse import quote

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


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


from jupyterhub.tests.test_api import api_request, add_user


@pytest.mark.parametrize("username", ["zoe", "50fia", "秀樹", "~TestJH", "has@"])
async def test_check_routes(app, disable_check_routes, username):
    proxy = app.proxy
    test_user = add_user(app.db, app, name=username)
    r = await api_request(app, "users/%s/server" % username, method="post")
    r.raise_for_status()

    # check a valid route exists for user
    routes = await app.proxy.get_all_routes()
    before = sorted(routes)
    assert test_user.proxy_spec in before

    # check if a route is removed when user deleted
    await app.proxy.check_routes(app.users, app._service_map)
    await proxy.delete_user(test_user)
    routes = await app.proxy.get_all_routes()
    during = sorted(routes)
    assert test_user.proxy_spec not in during

    # check if a route exists for user
    await app.proxy.check_routes(app.users, app._service_map)
    routes = await app.proxy.get_all_routes()
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
