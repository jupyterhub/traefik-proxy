"""Tests for the base traefik proxy"""

import pytest
import utils

from urllib.parse import urlparse
from jupyterhub.utils import exponential_backoff
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


async def test_etcd_routing(etcd, clean_etcd, proxy, launch_backends):
    routespec = ["/", "/user/first", "/user/second"]
    target = ["http://127.0.0.1:9000", "http://127.0.0.1:9090", "http://127.0.0.1:9099"]
    data = [{}, {}, {}]

    routes_no = len(target)
    traefik_port = urlparse(proxy.public_url).port

    # Check if traefik process is reacheable
    await exponential_backoff(
        utils.check_host_up, "Traefik not reacheable", ip="localhost", port=traefik_port
    )

    # Check if backends are reacheable
    await exponential_backoff(utils.check_backends_up, "Backends not reacheable")

    # Add testing routes
    await proxy.add_route(routespec[0], target[0], data[0])
    await proxy.add_route(routespec[1], target[1], data[1])
    await proxy.add_route(routespec[2], target[2], data[2])

    if proxy.public_url.endswith("/"):
        req_url = proxy.public_url[:-1]
    else:
        req_url = proxy.public_url

    await utils.check_routing(req_url)


async def test_host_origin_headers(etcd, clean_etcd, proxy, default_backend):
    routespec = "/user/username"
    target = "http://127.0.0.1:9000"
    data = {}

    traefik_port = urlparse(proxy.public_url).port
    traefik_host = urlparse(proxy.public_url).hostname
    default_backend_port = 9000

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


async def test_traefik_api_without_auth(etcd, clean_etcd, proxy, default_backend):
    traefik_port = urlparse(proxy.public_url).port

    await exponential_backoff(
        utils.check_host_up, "Traefik not reacheable", ip="localhost", port=traefik_port
    )

    try:
        resp = await AsyncHTTPClient().fetch(proxy.traefik_api_url + "/dashboard")
        rc = resp.code
    except ConnectionRefusedError:
        rc = None
    except Exception as e:
        rc = e.response.code
    finally:
        assert rc in {401, 403}


async def test_traefik_api_wit_auth(etcd, clean_etcd, proxy, default_backend):
    traefik_port = urlparse(proxy.public_url).port

    await exponential_backoff(
        utils.check_host_up, "Traefik not reacheable", ip="localhost", port=traefik_port
    )

    print(proxy.traefik_api_username)
    print(proxy.traefik_api_password)

    try:
        resp = await AsyncHTTPClient().fetch(
            proxy.traefik_api_url + "/dashboard",
            auth_username=proxy.traefik_api_username,
            auth_password=proxy.traefik_api_password,
        )

        rc = resp.code
        print(rc)
    except ConnectionRefusedError:
        rc = None
    except Exception as e:
        rc = e.response.code
    finally:
        assert rc == 200
