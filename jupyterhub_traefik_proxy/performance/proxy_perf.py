import argparse
import asyncio
import time
import textwrap

import matplotlib.pyplot as plt
from threading import Thread

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
        traefik_api_username="api_admin",
        should_start=True,
    )
    await proxy.start()
    return proxy


async def toml_proxy():
    """Function returning a configured TraefikTomlProxy"""
    proxy = TraefikTomlProxy(
        public_url="http://127.0.0.1:8000",
        traefik_api_password="admin",
        traefik_api_username="api_admin",
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
    if proxy_class == "TraefikTomlProxy":
        proxy = await toml_proxy()
    elif proxy_class == "TraefikEtcdProxy":
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


async def measure_methods_performance(proxy_class, iterations):
    proxy = await get_proxy(proxy_class)

    result = await performance_tests.measure_methods_perf(proxy, iterations)

    print("add_route took: " + str(result["add"]))
    print("delete_route took: " + str(result["delete"]))
    print("get_all_routes took: " + str(result["get_all"]))

    await stop_proxy(proxy_class, proxy)
    return result


async def measure_proxy_throughput(
    proxy_class, requests_no, concurrent_no, proto, request_size
):
    proxy = await get_proxy(proxy_class)

    routespec = "/some_routespec/"
    backend_port = 9000
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
        default="TraefikTomlProxy",
        help=textwrap.dedent(
            """\
            Proxy class to analyze.
            Available proxies:
            -TraefikTomlProxy
            -TraefikEtcdProxy
            -CHP
            If no proxy is provided, it defaults to:
            --- %(default)s ---
            """
        ),
    )

    args = parser.parse_args()
    print(args)
    metric = args.metric
    proxy_class = args.proxy_class

    requests_no = 1000
    concurrent_no = 10
    iterations = 1000

    loop = asyncio.get_event_loop()
    if metric == "http_throughput_small":
        result = loop.run_until_complete(
            measure_proxy_throughput(
                proxy_class, requests_no, concurrent_no, "http", "small"
            )
        )
        print("Request throughput small requests: " + str(result))
    elif metric == "http_throughput_large":
        result = loop.run_until_complete(
            measure_proxy_throughput(
                proxy_class, requests_no, concurrent_no, "http", "large"
            )
        )
        print("Request throughput large requests: " + str(result))
    elif metric == "ws_throughput":
        result = loop.run_until_complete(
            measure_proxy_throughput(
                proxy_class, requests_no, concurrent_no, "ws", "small"
            )
        )
    elif metric == "methods":
        result = loop.run_until_complete(
            measure_methods_performance(proxy_class, iterations)
        )


if __name__ == "__main__":
    main()
