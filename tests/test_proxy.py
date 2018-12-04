"""Tests for the base traefik proxy"""

import pytest
import json

# mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


async def test_add_route(proxy):
    # with pytest.raises(NotImplementedError):
    await proxy.add_route("/prefix", "http://127.0.0.1:99", {"test": "test0"})
    await proxy.add_route("/prefix0", "http://127.0.0.1:1000", {"test": "test0"})
    await proxy.stop()
    # print("route is " + route)
    # TODO: test the route


async def test_get_all_routes(proxy):
    # with pytest.raises(NotImplementedError):
    routes = await proxy.get_all_routes()
    print(json.dumps(routes, sort_keys=True, indent=4, separators=(',', ': ')))
    await proxy.stop()
    # TODO: test the routes


async def test_delete_route(proxy):
    # with pytest.raises(NotImplementedError):
    await proxy.delete_route("/prefix0")
    await proxy.stop()


async def test_get_route(proxy):
    # with pytest.raises(NotImplementedError):
    route = await proxy.get_route("/prefix")
    print(json.dumps(route, sort_keys=True, indent=4, separators=(',', ': ')))
    await proxy.stop()
    # TODO: test the route
