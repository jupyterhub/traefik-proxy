import socket
import json
from tornado.httpclient import AsyncHTTPClient

_ports = {"default_backend": 9000, "first_backend": 9090, "second_backend": 9099}


def get_port(service_name):
    return _ports[service_name]


def is_open(ip, port):
    timeout = 1
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, port))
        s.shutdown(socket.SHUT_RDWR)
        return True
    except:
        return False
    finally:
        s.close()


async def check_host_up(ip, port):
    """ Check if the service opened the connection on the
    designated port """
    return is_open(ip, port)


async def traefik_routes_to_correct_backend(traefik_url, path, expected_port):
    """ Check if traefik followed the configuration and routed the
    request to the right backend """
    print(traefik_url + path)
    resp = await AsyncHTTPClient().fetch(traefik_url + path)
    data = json.loads(resp.body)
    assert data == expected_port


def get_backend_ports():
    default_backend_port = get_port("default_backend")
    first_backend_port = get_port("first_backend")
    second_backend_port = get_port("second_backend")
    return default_backend_port, first_backend_port, second_backend_port


async def check_backends_up():
    """ Verify if the backends started listening on their designated
    ports """
    default_backend_port, first_backend_port, second_backend_port = get_backend_ports()
    default_up = await check_host_up("localhost", default_backend_port) == True
    first_up = await check_host_up("localhost", first_backend_port) == True
    second_up = await check_host_up("localhost", second_backend_port) == True

    return default_up and first_up and second_up


async def check_routing(traefik_url):
    default_backend_port, first_backend_port, second_backend_port = get_backend_ports()
    """ Send GET requests for resources on different paths and check
    they are routed based on their path-prefixes """
    await traefik_routes_to_correct_backend(
        traefik_url, "/otherthings/", default_backend_port
    )
    await traefik_routes_to_correct_backend(
        traefik_url, "/user/somebody/", default_backend_port
    )
    await traefik_routes_to_correct_backend(
        traefik_url, "/user/first/", first_backend_port
    )
    await traefik_routes_to_correct_backend(
        traefik_url, "/user/second/", second_backend_port
    )
    await traefik_routes_to_correct_backend(
        traefik_url, "/user/first/otherthings/", first_backend_port
    )
    await traefik_routes_to_correct_backend(
        traefik_url, "/user/second/otherthings/", second_backend_port
    )
