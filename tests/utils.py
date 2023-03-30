import json
import socket
import ssl
from urllib.parse import urlparse

from tornado.httpclient import AsyncHTTPClient, HTTPClientError, HTTPRequest

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
    """Check if the service opened the connection on the
    designated port"""
    return is_open(ip, port)


async def check_host_up_http(url):
    """Check if an HTTP endpoint is ready

    A socket listening may not be enough
    """
    u = urlparse(url)
    # first, check the scket
    socket_open = is_open(u.hostname, u.port or 80)
    if not socket_open:
        return False
    req = HTTPRequest(url, validate_cert=False)
    try:
        await AsyncHTTPClient().fetch(req)
    except HTTPClientError as e:
        if e.code >= 599:
            # connection error
            return False
    except (OSError, ssl.SSLError):
        # Can occur if SSL isn't set up yet
        return False
    return True


async def get_responding_backend_port(traefik_url, path):
    """Check if traefik followed the configuration and routed the
    request to the right backend"""

    headers = {}

    if not path.startswith("/"):
        host, slash, path = path.partition("/")
        path = slash + path
        headers["Host"] = host

    req = HTTPRequest(
        traefik_url + path,
        headers=headers,
        validate_cert=False,
        follow_redirects=True,
    )

    try:
        resp = await AsyncHTTPClient().fetch(req)
        return json.loads(resp.body)
    except HTTPClientError as e:
        raise e


async def check_services_ready(urls):
    ready = True
    for url in urls:
        ip = urlparse(url).hostname
        port = urlparse(url).port
        status = await check_host_up(ip=ip, port=port)
        ready = ready and status

    return ready
