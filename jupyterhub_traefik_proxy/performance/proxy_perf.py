import argparse
import asyncio
import os
import time
import textwrap

import csv
import matplotlib.pyplot as plt
import numpy as np
from threading import Thread
from statistics import mean

from jupyterhub.tests.mocking import MockHub
from jupyterhub.proxy import ConfigurableHTTPProxy
from jupyterhub_traefik_proxy import TraefikEtcdProxy
from jupyterhub_traefik_proxy import TraefikTomlProxy
from jupyterhub_traefik_proxy import performance_tests


async def no_auth_etcd_proxy():
    """
    Function returning a configured TraefikEtcdProxy.
    No etcd authentication.
    """
    proxy = TraefikEtcdProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="admin",
        should_start=True,
    )
    await proxy.start()
    time.sleep(5)
    return proxy


async def toml_proxy():
    """Function returning a configured TraefikTomlProxy"""
    proxy = TraefikTomlProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="admin",
        should_start=True,
    )

    await proxy.start()
    time.sleep(5)
    return proxy


async def configurable_http_proxy():
    """Function returning a configured ConfigurableHTTPProxy"""
    proxy = ConfigurableHTTPProxy(
        auth_token="secret!",
        api_url="http://127.0.0.1:54321",
        should_start=True,
        public_url="http://127.0.0.1:8000",
    )

    app = MockHub()
    app.init_hub()
    proxy.app = app
    proxy.hub = app.hub

    await proxy.start()
    return proxy


async def get_proxy(proxy_class):
    if proxy_class == "TomlProxy":
        proxy = await toml_proxy()
    elif proxy_class == "EtcdProxy":
        proxy = await no_auth_etcd_proxy()
    elif proxy_class == "CHP":
        proxy = await configurable_http_proxy()
    else:
        print("Proxy version not supported")
        return

    return proxy


async def stop_proxy(proxy_class, proxy):
    if proxy_class == "CHP":
        proxy.stop()
    else:
        await proxy.stop()


def get_tasks_list_results(tasks):
    results = [-1] * len(tasks)
    for task in tasks:
        route_idx, time_taken = task.result()
        results[route_idx] = time_taken

    return results


def ns_to_s(t):
    return t / 1000000000


async def measure_methods_performance_concurrent(proxy_class, iterations):
    proxy = await get_proxy(proxy_class)

    # Get "add_route" performance
    tasks = [
        performance_tests.add_route_perf(proxy, route_idx)
        for route_idx in range(iterations)
    ]
    
    _done, _running = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
    add = get_tasks_list_results(_done)
    mean_add = ns_to_s(mean(add))
    print(f"Add {mean_add}")

    # Get "get_all_routes" performance
    tasks = [
        performance_tests.get_all_routes_perf(proxy, route_idx)
        for route_idx in range(iterations)
    ]
    _done, _running = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
    get_all = get_tasks_list_results(_done)
    mean_get_all = ns_to_s(mean(get_all))
    print(f"Get all {mean_get_all}")

    # Get "delete_route" performance
    tasks = [
        performance_tests.delete_route_perf(proxy, route_idx)
        for route_idx in range(iterations)
    ]
    _done, _running = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
    delete = get_tasks_list_results(_done)
    mean_delete = ns_to_s(mean(delete))
    print(f"Delete {mean_delete}")

    await stop_proxy(proxy_class, proxy)
    result = {}
    result["add"] = add
    result["delete"] = delete
    result["get_all"] = get_all

    return result


async def measure_methods_performance(proxy_class, iterations):
    proxy = await get_proxy(proxy_class)

    for route_idx in range(iterations):
        time.sleep(2)
        _done, _running = await asyncio.wait(
            [performance_tests.add_route_perf(proxy, route_idx)],
            return_when=asyncio.ALL_COMPLETED,
        )
        add = get_tasks_list_results(_done)

    await stop_proxy(proxy_class, proxy)
    result = {}
    result["add"] = add
    return result


async def measure_proxy_throughput(
    proxy_class, requests_no, concurrent_no, proto, request_size, backend_port
):
    proxy = await get_proxy(proxy_class)

    routespec = "/some_routespec/"
    target = proto + "://127.0.0.1:" + str(backend_port)
    data = {"test": "test1", "user": "username"}
    await proxy.add_route(routespec, target, data)

    throughput = await performance_tests.measure_throughput(
        proxy, requests_no, concurrent_no, routespec, proto, request_size
    )

    print("Throughput is: " + str(throughput))
    await stop_proxy(proxy_class, proxy)

    return throughput


def main():
    parser = argparse.ArgumentParser(
        description="Performance measurement utility",
        epilog=textwrap.dedent(
            """\
            Available measurements:
            - Proxy methods:
                - add_route
                - delete_route
                - get_all_routes
            - Request throughput: small requests
            - Request throughput: large requests
            - Websocket throughput
            """
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--measure",
        dest="metric",
        default="methods",
        help=textwrap.dedent(
            """\
            What metric to measure. Available metrics:
            - methods
            - http_throughput_small
            - http_throughput_large
            - ws_throughput
            If no metric is provided, it defaults to:
            --- %(default)s ---
            """
        ),
    )

    parser.add_argument(
        "--proxy",
        dest="proxy_class",
        default="TomlProxy",
        help=textwrap.dedent(
            """\
            Proxy class to analyze.
            Available proxies:
            -TomlProxy
            -EtcdProxy
            -CHP
            If no proxy is provided, it defaults to:
            --- %(default)s ---
            """
        ),
    )

    parser.add_argument(
        "--routes_number",
        dest="routes_number",
        default=10,
        help=textwrap.dedent(
            """\
            Number of routes to be added/deleted/retrieved.
            If no number is provided, it defaults to:
            --- %(default)s ---
            """
        ),
    )

    parser.add_argument(
        "--concurrent_requests_number",
        dest="concurrent_requests_number",
        default=10,
        help=textwrap.dedent(
            """\
            Number of concurrent requests when comoputing the throughput.
            If no number is provided, it defaults to:
            --- %(default)s ---
            """
        ),
    )

    parser.add_argument(
        "--output",
        dest="csv_filename",
        help=textwrap.dedent(
            """
            The csv file name where the results will be stored.
            If no file is provided, the results will only be outputed to stdout.
            """
        ),
    )

    parser.add_argument(
        "--backend_port",
        dest="backend_port",
        default=9000,
        help=textwrap.dedent(
            """
            The port where the backend receives http/websocket requests.
            If no port is provided, it defaults to:
            --- %(default)s ---
            """
        ),
    )

    args = parser.parse_args()
    metric = args.metric
    proxy_class = args.proxy_class
    routes_number = int(args.routes_number)
    concurrent_requests_number = int(args.concurrent_requests_number)
    csv_filename = args.csv_filename
    backend_port = args.backend_port

    requests_no = 1000
    test_iterations = 5

    loop = asyncio.get_event_loop()
    if metric == "methods":
        tic = time.perf_counter_ns()
        results = {}
        for i in range(test_iterations):
            results[i] = loop.run_until_complete(
                measure_methods_performance_concurrent(proxy_class, routes_number)
            )
        print(ns_to_s(time.perf_counter_ns() - tic))

        if csv_filename:
            with open(csv_filename, mode="w+") as csv_file:
                sample_no = 3
                if routes_number > 40:
                    sample_no = routes_number / 10

                samples = np.unique(
                    np.logspace(
                        0, np.log10(routes_number), sample_no, endpoint=False, dtype=int
                    )
                )
                print(samples)
                fieldnames = ["proxy", "test_id", "method", "route_idx", "time"]
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()

                for test_id in range(test_iterations):
                    for sample in samples:
                        constants = [proxy_class, test_id, "add_route", sample]
                        result_add_dict = dict(zip(fieldnames[:-1], constants))
                        constants[2] = "delete_route"
                        result_delete_dict = dict(zip(fieldnames[:-1], constants))
                        constants[2] = "get_all_routes"
                        result_get_all_dict = dict(zip(fieldnames[:-1], constants))

                        result_add_dict["time"] = results[test_id]["add"][sample]
                        result_delete_dict["time"] = results[test_id]["delete"][sample]
                        result_get_all_dict["time"] = results[test_id]["get_all"][sample]

                        writer.writerow(result_add_dict)
                        writer.writerow(result_delete_dict)
                        writer.writerow(result_get_all_dict)
    else:
        if metric == "http_throughput_small":
            result = {}
            for concurrent_req in range(1, concurrent_requests_number):
                result[concurrent_req] = loop.run_until_complete(
                    measure_proxy_throughput(
                        proxy_class, requests_no, concurrent_req, "http", "small"
                    )
                )
            print("Request throughput small requests: " + str(result))
        elif metric == "http_throughput_large":
            result = {}
            for concurrent_req in range(1, concurrent_requests_number):
                result[concurrent_req] = loop.run_until_complete(
                    measure_proxy_throughput(
                        proxy_class, requests_no, concurrent_req, "http", "large"
                    )
                )
            print("Request throughput large requests: " + str(result))
        elif metric == "ws_throughput":
            result = {}
            for concurrent_req in range(1, concurrent_requests_number):
                result[concurrent_req] = loop.run_until_complete(
                    measure_proxy_throughput(
                        proxy_class, requests_no, concurrent_req, "ws", "small"
                    )
                )
        if csv_filename:
            with open(csv_filename, mode="a+") as csv_file:
                fieldnames = [i for i in range(1, concurrent_requests_number)]
                fieldnames.insert(0, "Proxy")
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                result["Proxy"] = proxy_class
                if os.stat(csv_filename).st_size == 0:
                    writer.writeheader()
                writer.writerow(result)


if __name__ == "__main__":
    main()
