"""Tests for the base traefik proxy"""

import pytest
import utils

from urllib.parse import urlparse
from jupyterhub.utils import exponential_backoff
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPClientError
import json


# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


async def wait_for_services(proxy, target):
    # Wait until traefik and the backend are ready
    await exponential_backoff(
        utils.check_services_ready,
        "Service not reacheable",
        urls=[proxy.public_url, target],
    )


@pytest.mark.parametrize(
    "routespec, target, data, expected_output",
    [
        (
            "/user/username",
            "http://127.0.0.1:9000",
            {"test": "test1", "user": "username"},
            {
                "routespec": "/user/username",
                "target": "http://127.0.0.1:9000",
                "data": json.dumps({"test": "test1", "user": "username"}),
            },
        ),  # Path-based routing
        (
            "/user/user@email",
            "http://127.0.0.1:9900",
            {},
            {
                "routespec": "/user/user@email",
                "target": "http://127.0.0.1:9900",
                "data": "{}",
            },
        ),  # Path-based routing, no data dict
        (
            "host/proxy/path",
            "http://127.0.0.1:9009",
            {"test": "test2"},
            {
                "routespec": "host/proxy/path",
                "target": "http://127.0.0.1:9009",
                "data": json.dumps({"test": "test2"}),
            },
        ),  # Host-based routing
    ],
)
async def test_add_get_delete(
    proxy, launch_backend, routespec, target, data, expected_output
):
    backend_port = urlparse(target).port
    launch_backend(backend_port)
    await wait_for_services(proxy, target)

    """ Test add and get """
    await proxy.add_route(routespec, target, data)
    # Make sure the route was added
    route = await proxy.get_route(routespec)
    assert route == expected_output

    if proxy.public_url.endswith("/"):
        req_url = proxy.public_url[:-1]
    else:
        req_url = proxy.public_url
    # Test the actual routing
    responding_backend1 = await utils.get_responding_backend_port(req_url, routespec)
    responding_backend2 = await utils.get_responding_backend_port(
        req_url, routespec + "/something"
    )
    assert responding_backend1 == backend_port and responding_backend2 == backend_port

    """ Test delete + get """
    await proxy.delete_route(routespec)
    route = await proxy.get_route(routespec)
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


async def test_host_origin_headers(proxy, launch_backend):
    routespec = "/user/username"
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
