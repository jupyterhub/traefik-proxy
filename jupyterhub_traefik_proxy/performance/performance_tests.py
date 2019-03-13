import asyncio
import concurrent.futures
from numpy import mean
import time
import subprocess
import sys
import websockets

import urllib.request
from urllib.parse import urlparse
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from os.path import dirname, join, abspath
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor


async def measure_add_route(proxy, routespec, target, data):
    tic = time.perf_counter_ns()
    await proxy.add_route(routespec, target, data)
    return time.perf_counter_ns() - tic


async def measure_delete_route(proxy, routespec):
    tic = time.perf_counter_ns()
    await proxy.delete_route(routespec)
    return time.perf_counter_ns() - tic


async def measure_get_all_routes(proxy):
    tic = time.perf_counter_ns()
    await proxy.get_all_routes()
    return time.perf_counter_ns() - tic


async def add_route_perf(proxy, routes_no):
    target = "http://127.0.0.1:9000"
    data = {"test": "test1", "user": "username"}

    times = []
    for i in range(routes_no):
        routespec = "/route/" + str(i) + "/"
        result = await measure_add_route(proxy, routespec, target, data)
        times.append(result)
    return mean(times)


async def delete_route_perf(proxy, routes_no):
    times = []
    for i in range(routes_no):
        routespec = "/route/" + str(i) + "/"
        result = await measure_delete_route(proxy, routespec)
        times.append(result)
    return mean(times)


async def get_all_routes_perf(proxy, routes_no):
    times = []
    for i in range(routes_no):
        result = await measure_get_all_routes(proxy)
        times.append(result)
    return mean(times)


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


async def measure_methods_perf(proxy, routes_no):
    result = {}

    mean_add = await add_route_perf(proxy, routes_no)
    mean_get_all = await get_all_routes_perf(proxy, routes_no)
    mean_delete = await delete_route_perf(proxy, routes_no)

    result["add"] = mean_add
    result["get_all"] = mean_get_all
    result["delete"] = mean_delete

    return result


async def measure_throughput(
    proxy, requests_no, concurrent_no, routespec, proto, request_size
):
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
