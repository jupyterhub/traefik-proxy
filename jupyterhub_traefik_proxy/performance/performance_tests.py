import asyncio
import time

from numpy import mean
from urllib.parse import urlparse
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import websockets


async def add_route_perf(proxy, route_idx):
    """
    Computes time taken (ns) to add the "route_idx"
    route to the proxy's routing table ( which
    contains route_idx - 1 routes).

    Returns a tuple:
    [
        route_idx: the index of the route added
        time_taken: the time it took to add the route with number 
                  "route_idx" to the proxy's routing table
    ]
    """
    target = "http://127.0.0.1:9000"
    data = {"test": "test_" + str(route_idx), "user": "user_" + str(route_idx)}
    routespec = "/route/" + str(route_idx) + "/"

    tic = time.perf_counter_ns()
    await proxy.add_route(routespec, target, data)
    time_taken = time.perf_counter_ns() - tic

    return route_idx, time_taken


async def delete_route_perf(proxy, route_idx):
    """
    Computes time taken (ns) to delete the "route_idx"
    route from the proxy's routing table (which 
    contains route_idx + 1 routes).
    
    It assumes the route to be deleted already exists.

    Returns a tuple:
    [
        route_idx: the index of the route deleted
        time_taken: the time it took to delete the route with number 
                  "route_idx" from the proxy's routing table
    ]
    """
    routespec = "/route/" + str(route_idx) + "/"

    tic = time.perf_counter_ns()
    await proxy.delete_route(routespec)
    time_taken = time.perf_counter_ns() - tic

    return route_idx, time_taken


async def get_all_routes_perf(proxy, iteration):
    """
    Computes time taken (ns) to retrieve all the
    routes from the proxy's routing table.

    Returns a tuple:
    [
        iteration: the iteration index
        time_taken: the time it took to get all the routes
    ]
    """
    tic = time.perf_counter_ns()
    await proxy.get_all_routes()
    time_taken = time.perf_counter_ns() - tic
    return iteration, time_taken


def create_request_url(proxy, routespec, proto):
    if proto == "http":
        return proxy.public_url + routespec
    req_url = "ws://" + urlparse(proxy.public_url).netloc + routespec
    return req_url


async def make_http_req(proxy, routespec, request_size):
    req_url = create_request_url(proxy, routespec, "http")
    req = HTTPRequest(req_url, method="GET", headers={"RequestSize": request_size})
    resp = await AsyncHTTPClient().fetch(req)
    return resp


async def make_ws_small_req(proxy, routespec):
    req_url = create_request_url(proxy, routespec, "ws")
    async with websockets.connect(req_url) as websocket:
        resp = await websocket.recv()

    return resp


async def measure_throughput(
    proxy, requests_no, concurrent_no, routespec, proto, request_size
):
    """
    Makes 'requests_no' GET http/websocket requests
    to the proxy with max 'concurrent_no' concurrent.

    Returns the throughput(number of requests/milisec)
    """
    loop = asyncio.get_event_loop()
    running_tasks = set()

    tic = time.perf_counter_ns()
    for i in range(requests_no):
        if len(running_tasks) == concurrent_no:
            # Wait for some task to finish before adding a new one
            _done, running_tasks = await asyncio.wait(
                running_tasks, return_when=asyncio.FIRST_COMPLETED
            )
        if proto == "http":
            running_tasks.add(
                loop.create_task(make_http_req(proxy, routespec, request_size))
            )
        else:
            running_tasks.add(loop.create_task(make_ws_small_req(proxy, routespec)))
    res = await asyncio.wait(running_tasks, return_when=asyncio.ALL_COMPLETED)
    tac = time.perf_counter_ns()
    time_taken = tac - tic
    print("time taken: " + str(time_taken))

    requests_per_milisec = (requests_no * 1000000000) / time_taken

    return requests_per_milisec
