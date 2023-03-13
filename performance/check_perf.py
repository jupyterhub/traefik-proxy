import asyncio
import csv
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from urllib.parse import urlparse

import requests
import websockets

performance_dir = Path(__file__).parent.resolve()

sys.path.insert(0, performance_dir)
import perf_utils


async def add_route_perf(proxy, route_idx, stdout_print):
    """
    Computes time taken (ns) to add the "route_idx"
    route to the proxy's routing table (which
    contains route_idx - 1 routes when ran sequentially).

    Returns a tuple:
    [
        route_idx(int):   the index of the route added
        time_taken(dict): the time it took to add the route
                          number "route_idx" to the proxy's
                          routing table.
                          keys:
                             'cpu': CPU time, 'time.process_time()'
                             'real': Real time, 'time.perf_counter()'
    ]
    """
    target = "http://127.0.0.1:9000"
    data = {"test": "test_" + str(route_idx), "user": "user_" + str(route_idx)}
    routespec = "/route/" + str(route_idx) + "/"
    time_taken = {}

    with perf_utils.measure_time(
        f"adding route_{route_idx}, took", stdout_print, time_taken
    ):
        await proxy.add_route(routespec, target, data)

    return route_idx, time_taken


async def delete_route_perf(proxy, route_idx, stdout_print):
    """
    Computes time taken (ns) to delete the "route_idx"
    route from the proxy's routing table (which
    contains route_idx + 1 routes when ran sequentially).

    It assumes the route to be deleted exists.

    Returns a tuple:
    [
        route_idx(int):   the index of the route deleted
        time_taken(dict): the time it took to delete the route
                          number "route_idx" from the proxy's
                          routing table.
                          keys:
                             'cpu': CPU time, 'time.process_time()'
                             'real': Real time, 'time.perf_counter()'
    ]
    """
    routespec = "/route/" + str(route_idx) + "/"
    time_taken = {}

    with perf_utils.measure_time(
        f"deleting route_{route_idx}, took", stdout_print, time_taken
    ):
        await proxy.delete_route(routespec)

    return route_idx, time_taken


async def get_all_routes_perf(proxy, iteration, stdout_print):
    """
    Computes time taken (ns) to retrieve all the
    routes from the proxy's routing table.

    Returns a tuple:
    [
        iteration(int):   the iteration index
        time_taken(dict): the time it took to get all the routes
                          keys:
                             'cpu': CPU time, 'time.process_time()'
                             'real': Real time, 'time.perf_counter()'
    ]
    """
    time_taken = {}
    with perf_utils.measure_time(
        f"getting all routes iteration_{iteration} took", stdout_print, time_taken
    ):
        await proxy.get_all_routes()

    return iteration, time_taken


async def run_methods_concurrent(method, proxy, routes, stdout_print, concurrency):
    semaphore = asyncio.BoundedSemaphore(concurrency)

    async def run_one(route_idx):
        # measurement: include wait for semaphore?
        # outer_time = {}
        # with perf_utils.measure_time(
        #     f"Awaiting {method.__name__} for route {route_idx}, took",
        #     stdout_print,
        #     outer_time,
        # ):
        async with semaphore:
            _, time_taken = await method(proxy, route_idx, stdout_print)
            # time_taken["full"] = outer_time["real"]
        return route_idx, time_taken

    tasks = [asyncio.ensure_future(run_one(route_idx)) for route_idx in range(routes)]
    with perf_utils.measure_time(
        f"Running {method.__name__} for {routes} total routes, took", True, {}
    ):
        _done, _running = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
    results = {}
    for route_idx, times in await asyncio.gather(*tasks):
        results[route_idx] = times
    return results


async def measure_methods_performance(
    concurrency,
    proxy_class,
    routes,
    stdout_print=True,
):
    async with perf_utils.get_proxy(proxy_class) as proxy:
        run = partial(
            run_methods_concurrent,
            concurrency=concurrency,
            proxy=proxy,
            routes=routes,
            stdout_print=stdout_print,
        )

        result = {}
        result["add"] = await run(add_route_perf)
        result["get_all"] = await run(get_all_routes_perf)
        result["delete"] = await run(delete_route_perf)

    return result


def make_http_req(public_url, routespec, request_size):
    """request functions run in the background via process pool"""
    req_url = public_url + routespec
    r = requests.get(req_url, headers={"Request-Size": request_size})
    r.raise_for_status()


def make_ws_req(public_url, routespec, request_size):
    """request functions run in the background via process pool"""
    netloc = urlparse(public_url).netloc
    req_url = f"ws://{netloc}{routespec}ws/{request_size}"

    async def f():
        async with websockets.connect(req_url) as websocket:
            msg = await websocket.recv()
            while msg != "":
                msg = await websocket.recv()

    asyncio.run(f())


async def measure_proxy_throughput(
    proxy_class,
    total_requests,
    concurrent_no,
    proto,
    request_size,
    backend_port,
    stdout_print=True,
):
    """
    Makes 'total_requests' GET http/websocket requests
    to the proxy with max 'concurrent_no' concurrent.

    Returns the throughput(number of requests/milisec)
    """
    pool = ProcessPoolExecutor(concurrent_no)

    async with perf_utils.get_proxy(proxy_class) as proxy:
        routespec = "/some_routespec/"
        target = "http://127.0.0.1:" + str(backend_port)
        data = {"test": "test1", "user": "username"}
        await proxy.add_route(routespec, target, data)

        asyncio.get_running_loop()

        time_taken = {}

        with perf_utils.measure_time(
            f"The {total_requests} {request_size} {proto} reqests with {concurrent_no} running concurrently, took",
            stdout_print,
            time_taken,
        ):
            if proto == "http":
                make_req = make_http_req
            else:
                make_req = make_ws_req
            tasks = [
                asyncio.wrap_future(
                    pool.submit(make_req, proxy.public_url, routespec, request_size)
                )
                for i in range(total_requests)
            ]
            await asyncio.gather(*tasks)

        real_time = time_taken["real"]

        throughput = total_requests / real_time
        print(
            f"{concurrent_no} concurrent requests: throughput = {throughput:.3f} requests/s\n"
        )

    return throughput


async def main():
    parser = perf_utils.configure_argument_parser()

    args = parser.parse_args()
    metric = args.metric
    concurrency = int(args.concurrency)
    proxy_class = args.proxy_class
    routes = int(args.routes)
    total_requests = int(args.total_requests)
    csv_filename = args.csv_filename
    test_iterations = int(args.test_iterations)
    print(args)

    loop = asyncio.get_running_loop()
    if not csv:
        loop.set_debug(True)  # Enable debug if we're just printing the results

    if metric == "methods":
        results = {}
        for i in range(test_iterations):
            print(
                f"Starting {metric} {concurrency=} measurement number {i} for {proxy_class} ...\n"
            )
            results[i] = await measure_methods_performance(
                concurrency, proxy_class, routes, csv_filename is None
            )

        if csv_filename:
            with open(csv_filename, mode="a+") as csv_file:
                samples = perf_utils.logspace_samples(routes)
                const_fields = {
                    "proxy": proxy_class,
                    "concurrency": concurrency,
                    "total_routes": routes,
                }
                fieldnames = list(const_fields.keys()) + [
                    "test_id",
                    "method",
                    "route_idx",
                    "cpu_time",
                    "real_time",
                ]
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                if os.stat(csv_filename).st_size == 0:
                    writer.writeheader()

                perf_utils.persist_methods_results_to_csv(
                    writer,
                    results,
                    test_iterations,
                    samples,
                    const_fields,
                )
    else:
        print(f"Started measuring {metric}")
        print(
            f"Running {total_requests} requests with up to {concurrency} concurrent...\n"
        )
        results = {}
        kind, _, size = metric.split("_")

        async with perf_utils.backend(concurrency) as backend_port:
            for i in range(test_iterations):
                results[i] = await measure_proxy_throughput(
                    proxy_class,
                    total_requests,
                    concurrency,
                    kind,
                    size,
                    backend_port,
                    not csv_filename,
                )

            print(f"Request throughput {size} {kind} requests: {results}")

        if csv_filename:
            with open(csv_filename, mode="a+") as csv_file:
                fieldnames = [
                    "test_id",
                    "throughput",
                ]
                const_fields = {
                    "proxy": proxy_class,
                    "kind": kind,
                    "size": size,
                    "total_requests": total_requests,
                    "concurrency": concurrency,
                }
                fieldnames.extend(const_fields.keys())
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                if os.stat(csv_filename).st_size == 0:
                    writer.writeheader()
                for i in range(test_iterations):
                    row = {}
                    row.update(const_fields)
                    row["test_id"] = i
                    row["throughput"] = results[i]
                    writer.writerow(row)


if __name__ == "__main__":
    asyncio.run(main())
