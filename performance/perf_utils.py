import argparse
import asyncio
import logging
import sys
import textwrap
import time
from contextlib import asynccontextmanager, contextmanager, nullcontext
from inspect import isawaitable
from multiprocessing import cpu_count
from pathlib import Path
from subprocess import Popen
from tempfile import TemporaryDirectory

import aiohttp
import numpy as np
from jupyterhub.proxy import ConfigurableHTTPProxy
from jupyterhub.tests.mocking import MockHub
from jupyterhub.utils import wait_for_http_server

from jupyterhub_traefik_proxy.consul import TraefikConsulProxy
from jupyterhub_traefik_proxy.etcd import TraefikEtcdProxy
from jupyterhub_traefik_proxy.fileprovider import TraefikFileProviderProxy

aiohttp.TCPConnector.__init__.__kwdefaults__['limit'] = 10

performance_dir = Path(__file__).parent.resolve()


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
        "metric",
        nargs="?",
        default="methods",
        choices=[
            "methods",
            "http_throughput_small",
            "http_throughput_large",
            "ws_throughput_small",
            "ws_throughput_large",
        ],
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
        default="file",
        help=textwrap.dedent(
            """\
            Proxy class to analyze.
            Available proxies:
            - file
            - etcd
            - consul
            - chp
            If no proxy is provided, it defaults to:
            --- %(default)s ---
            """
        ),
    )

    parser.add_argument(
        "--routes",
        dest="routes",
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
        "-j",
        "--concurrency",
        dest="concurrency",
        default=10,
        help=textwrap.dedent(
            """\
            Number of concurrent requests when computing the throughput.
            Number of concurrent API calls when computing method performance.
            If no number is provided, it defaults to:
            --- %(default)s ---
            """
        ),
    )

    parser.add_argument(
        "--requests",
        dest="total_requests",
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

    return parser


@contextmanager
def etcd():
    """Context manager for running etcd"""
    with TemporaryDirectory() as td:
        p = Popen(['etcd'], cwd=td)
        # wait for it to start
        time.sleep(5)
        try:
            yield
        finally:
            try:
                p.terminate()
            except Exception as e:
                print(f"Error stopping {p}: {e}", file=sys.stderr)


@contextmanager
def consul():
    """Context manager for running consul"""
    with TemporaryDirectory() as td:
        p = Popen(['consul', 'agent', '-dev'], cwd=td)
        # wait for it to start
        time.sleep(5)
        try:
            yield
        finally:
            try:
                p.terminate()
            except Exception as e:
                print(f"Error stopping {p}: {e}", file=sys.stderr)


@asynccontextmanager
async def backend(concurrency=4):
    port = 9000
    # limit backend workers to 1 per CPU
    concurrency = min(concurrency, cpu_count())

    p = Popen(
        [
            "uvicorn",
            "dummy_http_server:app",
            f"--workers={concurrency}",
            f"--port={port}",
            "--log-level=warning",
        ],
        cwd=performance_dir,
    )
    try:
        await wait_for_http_server(f"http://127.0.0.1:{port}")
        yield port
    finally:
        try:
            p.terminate()
        except Exception as e:
            print(f"Error stopping {p}: {e}", file=sys.stderr)


@contextmanager
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
        # traefik_log_level="DEBUG",
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


async def file_proxy():
    """Function returning a configured TraefikFileProviderProxy"""
    proxy = TraefikFileProviderProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="admin",
        should_start=True,
        # traefik_log_level="DEBUG",
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


@asynccontextmanager
async def get_proxy(proxy_class):
    logging.basicConfig(level=logging.INFO)
    parent_context = nullcontext
    if proxy_class == "file":
        proxy_f = file_proxy
    elif proxy_class == "etcd":
        proxy_f = no_auth_etcd_proxy
        parent_context = etcd
    elif proxy_class == "consul":
        proxy_f = no_auth_consul_proxy
        parent_context = consul
    elif proxy_class == "chp":
        proxy_f = configurable_http_proxy
    else:
        raise ValueError(f"Proxy {proxy_class} not supported")
        return

    with parent_context():
        proxy = await proxy_f()
        try:
            yield proxy
        finally:
            stop = proxy.stop()
            if isawaitable(stop):
                await stop
    # let everything cleanup
    await asyncio.sleep(3)


def format_method_result(
    method,
    test_id,
    sample,
    results,
    const_fields,
):
    result = {}
    result.update(const_fields)
    result["method"] = method
    result["test_id"] = test_id
    result["route_idx"] = sample
    result["cpu_time"] = results[test_id][method][sample]["cpu"]
    result["real_time"] = results[test_id][method][sample]["real"]
    return result


def persist_methods_results_to_csv(
    csv_writer,
    results,
    test_iterations,
    samples,
    const_fields,
):
    for test_id in range(test_iterations):
        for sample in results[test_id]["add"].keys():
            result_add_dict = format_method_result(
                "add", test_id, sample, results, const_fields
            )
            result_delete_dict = format_method_result(
                "delete", test_id, sample, results, const_fields
            )

            csv_writer.writerow(result_add_dict)
            csv_writer.writerow(result_delete_dict)
            if sample in results[test_id]["get_all"]:
                result_get_all_dict = format_method_result(
                    "get_all",
                    test_id,
                    sample,
                    results,
                    const_fields,
                )
                csv_writer.writerow(result_get_all_dict)


def logspace_samples(routes):
    sample_no = 3
    if routes > 40:
        sample_no = routes // 10

    samples = np.unique(
        np.logspace(0, np.log10(routes), sample_no, endpoint=False, dtype=int)
    )
    return samples
