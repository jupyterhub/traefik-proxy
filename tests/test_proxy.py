"""Tests for the base traefik proxy"""

import pytest

# mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


async def test_add_route(proxy):
    with pytest.raises(NotImplementedError):
        route = await proxy.add_route("/prefix", "http://127.0.0.1:9999", {})
    # TODO: test the route


async def test_get_all_routes(proxy):
    with pytest.raises(NotImplementedError):
        routes = await proxy.get_all_routes()
    # TODO: test the routes


async def test_delete_route(proxy):
    with pytest.raises(NotImplementedError):
        await proxy.delete_route("/prefix")


async def test_get_route(proxy):
    with pytest.raises(NotImplementedError):
        route = await proxy.get_route("/prefix")
    # TODO: test the route
