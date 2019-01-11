import socket
import json

from jupyterhub.utils import exponential_backoff
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPClientError

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


async def get_responding_backend_port(traefik_url, path):
    """ Check if traefik followed the configuration and routed the
    request to the right backend """
    if not path.startswith("/"):
        req = HTTPRequest(
            traefik_url + "".join("/" + path.split("/", 1)[1]),
            method="GET",
            headers={"Host": path.split("/")[0]},
        )
    else:
        req = traefik_url + path

    try:
        resp = await AsyncHTTPClient().fetch(req)
        return json.loads(resp.body)
    except HTTPClientError as e:
        raise e


async def check_services_ready(ips, ports):
    ready = True
    for ip, port in zip(ips, ports):
        status = await check_host_up(ip=ip, port=port)
        ready = ready and status

    return ready
