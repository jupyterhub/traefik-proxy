import argparse
import contextlib
import textwrap
import time
from urllib.parse import urlparse

import numpy as np

from jupyterhub.tests.mocking import MockHub
from jupyterhub.proxy import ConfigurableHTTPProxy
from jupyterhub_traefik_proxy import TraefikConsulProxy
from jupyterhub_traefik_proxy import TraefikEtcdProxy
from jupyterhub_traefik_proxy import TraefikTomlProxy


def configure_argument_parser():
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
        "--concurrent",
        dest="concurrent",
        action="store_true",
        help=textwrap.dedent(
            """\
            Whether or not to run the methods concurrent.
            """
        ),
    )

    parser.add_argument(
        "--sequential",
        dest="concurrent",
        action="store_false",
        help=textwrap.dedent(
            """\
            Whether or not to run the methods sequentially.
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
            -ConsulProxy
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
            Number of concurrent requests when computing the throughput.
            If no number is provided, it defaults to:
            --- %(default)s ---
            """
        ),
    )

    parser.add_argument(
        "--total_requests_number",
        dest="total_requests_number",
        default=1000,
        help=textwrap.dedent(
            """\
            Total number of requests when computing the throughput.
            If no number is provided, it defaults to:
            --- %(default)s ---
            """
        ),
    )

    parser.add_argument(
        "--iterations",
        dest="test_iterations",
        default=1,
        help=textwrap.dedent(
            """
            How many times to run the measurement.
            If no value is provided, it defaults to:
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
            Note: Don't forget to start the backend on this port!
            """
        ),
    )

    return parser


@contextlib.contextmanager
def measure_time(print_message, stdout_print, time_taken):
    real_time = time.perf_counter()
    process_time = time.process_time()
    yield
    real_time = time.perf_counter() - real_time
    cpu_time = time.process_time() - process_time
    io_time = max(0.0, real_time - cpu_time)
    if stdout_print:
        print(f"{print_message}")
        print(f"CPU time:      {cpu_time:.3f} s")
        print(f"IO time:       {io_time:.3f} s")
        print(f"REAL time:     {real_time:.3f} s")
        # print()
    time_taken["cpu"] = cpu_time
    time_taken["real"] = real_time


async def no_auth_consul_proxy():
    """
    Function returning a configured TraefikEtcdProxy.
    No etcd authentication.
    """
    proxy = TraefikConsulProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="admin",
        should_start=True,
    )
    await proxy.start()
    return proxy


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
    elif proxy_class == "ConsulProxy":
        proxy = await no_auth_consul_proxy()
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


def get_tasks_result(tasks):
    results = {}
    for task in tasks:
        route_idx, time_taken = task.result()
        results[route_idx] = time_taken

    return results


def format_method_result(method, proxy_class, test_id, sample, fieldnames, results):
    constants = [proxy_class, test_id, method, sample]
    result = dict(zip(fieldnames[:-1], constants))
    result["cpu_time"] = results[test_id][method][sample]["cpu"]
    result["real_time"] = results[test_id][method][sample]["real"]
    return result


def persist_methods_results_to_csv(
    csv_writer, results, fieldnames, test_iterations, samples, proxy_class
):
    for test_id in range(test_iterations):
        for sample in samples:
            result_add_dict = format_method_result(
                "add", proxy_class, test_id, sample, fieldnames, results
            )
            result_delete_dict = format_method_result(
                "delete", proxy_class, test_id, sample, fieldnames, results
            )
            result_get_all_dict = format_method_result(
                "get_all", proxy_class, test_id, sample, fieldnames, results
            )

            csv_writer.writerow(result_add_dict)
            csv_writer.writerow(result_delete_dict)
            csv_writer.writerow(result_get_all_dict)


def logspace_samples(routes_number):
    sample_no = 3
    if routes_number > 40:
        sample_no = routes_number / 10

    samples = np.unique(
        np.logspace(0, np.log10(routes_number), sample_no, endpoint=False, dtype=int)
    )
    return samples


def create_request_url(proxy, routespec, proto):
    if proto == "http":
        return proxy.public_url + routespec
    req_url = "ws://" + urlparse(proxy.public_url).netloc + routespec
    return req_url
