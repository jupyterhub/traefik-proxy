import asyncio
import csv
import os
import time

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
import websockets

from . import perf_utils


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


async def run_methods_concurrent(method, proxy, routes_number, stdout_print):
    tasks = [
        method(proxy, route_idx, stdout_print) for route_idx in range(routes_number)
    ]
    with perf_utils.measure_time(
        f"Running {method.__name__} for {routes_number} total routes, took", True, {}
    ):
        _done, _running = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
    return _done


async def run_methods_sequentially(method, proxy, routes_number, stdout_print):
    res = {}
    with perf_utils.measure_time(
        f"Running {method.__name__} for {routes_number} total routes, took", True, {}
    ):
        for route_idx in range(routes_number):
            _, t = await method(proxy, route_idx, stdout_print)
            res[route_idx] = t

    return res


async def measure_methods_performance(
    concurrent, proxy_class, routes_number, stdout_print=True
):
    proxy = await perf_utils.get_proxy(proxy_class)

    add = {}
    delete = {}
    get_all = {}

    if concurrent:
        add = perf_utils.get_tasks_result(
            await run_methods_concurrent(
                add_route_perf, proxy, routes_number, stdout_print
            )
        )
        get_all = perf_utils.get_tasks_result(
            await run_methods_concurrent(
                get_all_routes_perf, proxy, routes_number, stdout_print
            )
        )
        delete = perf_utils.get_tasks_result(
            await run_methods_concurrent(
                delete_route_perf, proxy, routes_number, stdout_print
            )
        )
    else:
        add = await run_methods_sequentially(
            add_route_perf, proxy, routes_number, stdout_print
        )
        get_all = await run_methods_sequentially(
            get_all_routes_perf, proxy, routes_number, stdout_print
        )
        delete = await run_methods_sequentially(
            delete_route_perf, proxy, routes_number, stdout_print
        )

    await perf_utils.stop_proxy(proxy_class, proxy)

    result = {}
    result["add"] = add
    result["delete"] = delete
    result["get_all"] = get_all

    return result


async def make_http_req(proxy, routespec, request_size):
    req_url = perf_utils.create_request_url(proxy, routespec, "http")
    req = HTTPRequest(req_url, method="GET", headers={"RequestSize": request_size})
    resp = await AsyncHTTPClient().fetch(req)
    return resp


async def make_ws_small_req(proxy, routespec):
    req_url = perf_utils.create_request_url(proxy, routespec, "ws")
    async with websockets.connect(req_url) as websocket:
        resp = await websocket.recv()

    return resp


async def measure_proxy_throughput(
    proxy_class,
    total_requests_number,
    concurrent_no,
    proto,
    request_size,
    backend_port,
    stdout_print=True,
):
    """
    Makes 'total_requests_number' GET http/websocket requests
    to the proxy with max 'concurrent_no' concurrent.

    Returns the throughput(number of requests/milisec)
    """
    proxy = await perf_utils.get_proxy(proxy_class)
    routespec = "/some_routespec/"
    target = proto + "://127.0.0.1:" + str(backend_port)
    data = {"test": "test1", "user": "username"}
    await proxy.add_route(routespec, target, data)

    loop = asyncio.get_event_loop()
    running_tasks = set()

    time_taken = {}
    with perf_utils.measure_time(
        f"The {total_requests_number} {request_size} {proto} reqests with {concurrent_no} running concurrently, took",
        stdout_print,
        time_taken,
    ):
        for i in range(total_requests_number):
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
    real_time = time_taken["real"]

    throughput = total_requests_number / real_time
    print(
        f"{concurrent_no} concurrent requests: throughput = {throughput:.3f} requests/s\n"
    )

    await perf_utils.stop_proxy(proxy_class, proxy)

    return throughput


def main():
    parser = perf_utils.configure_argument_parser()

    args = parser.parse_args()
    metric = args.metric
    concurrent = args.concurrent
    proxy_class = args.proxy_class
    routes_number = int(args.routes_number)
    concurrent_requests_number = int(args.concurrent_requests_number)
    total_requests_number = int(args.total_requests_number)
    csv_filename = args.csv_filename
    backend_port = args.backend_port
    test_iterations = int(args.test_iterations)

    loop = asyncio.get_event_loop()
    if not csv:
        loop.set_debug(True)  # Enable debug if we're just printing the results

    if metric == "methods":
        results = {}
        for i in range(test_iterations):
            if concurrent:
                mode = "concurrent"
            else:
                mode = "sequentially"
            print(
                f"Starting {metric} {mode} measurement number {i} for {proxy_class} ...\n"
            )
            results[i] = loop.run_until_complete(
                measure_methods_performance(
                    concurrent, proxy_class, routes_number, csv_filename is None
                )
            )
        if csv_filename:
            with open(csv_filename, mode="w+") as csv_file:
                samples = perf_utils.logspace_samples(routes_number)
                fieldnames = [
                    "proxy",
                    "test_id",
                    "method",
                    "route_idx",
                    "cpu_time",
                    "real_time",
                ]
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()

                perf_utils.persist_methods_results_to_csv(
                    writer, results, fieldnames, test_iterations, samples, proxy_class
                )
    else:
        print(f"Started measuring {metric}")
        print(
            f"Running {total_requests_number} requests with up to {concurrent_requests_number} concurrent...\n"
        )
        if metric == "http_throughput_small":
            result = {}
            for i in range(test_iterations):
                result[i] = {}
                for concurrent_req in range(1, concurrent_requests_number + 1):
                    result[i][concurrent_req] = loop.run_until_complete(
                        measure_proxy_throughput(
                            proxy_class,
                            total_requests_number,
                            concurrent_req,
                            "http",
                            "small",
                            backend_port,
                            not csv_filename,
                        )
                    )
            print("Request throughput small http requests: " + str(result))
        elif metric == "http_throughput_large":
            result = {}
            for i in range(test_iterations):
                result[i] = {}
                for concurrent_req in range(1, concurrent_requests_number + 1):
                    result[i][concurrent_req] = loop.run_until_complete(
                        measure_proxy_throughput(
                            proxy_class,
                            total_requests_number,
                            concurrent_req,
                            "http",
                            "large",
                            backend_port,
                            not csv_filename,
                        )
                    )
            print("Request throughput large http requests: " + str(result))
        elif metric == "ws_throughput":
            result = {}
            for i in range(test_iterations):
                result[i] = {}
                for concurrent_req in range(1, concurrent_requests_number + 1):
                    result[i][concurrent_req] = loop.run_until_complete(
                        measure_proxy_throughput(
                            proxy_class,
                            total_requests_number,
                            concurrent_req,
                            "ws",
                            "small",
                            backend_port,
                            not csv_filename,
                        )
                    )
            print("Request throughput ws requests: " + str(result))
        if csv_filename:
            with open(csv_filename, mode="a+") as csv_file:
                fieldnames = [i for i in range(1, concurrent_requests_number + 1)]
                print(concurrent_requests_number)
                fieldnames.insert(0, "TestID")
                fieldnames.insert(0, "Proxy")
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                if os.stat(csv_filename).st_size == 0:
                    writer.writeheader()
                for i in range(test_iterations):
                    result[i]["Proxy"] = proxy_class
                    result[i]["TestID"] = i
                    writer.writerow(result[i])


if __name__ == "__main__":
    main()
