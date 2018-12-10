import time
import socket
import requests

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


def check_host_up(ip, port):
    """ Allow the service up to 2 sec to open connection on the
    designated port """
    up = False
    retry = 20  # iterations
    delay = 0.1  # 100 ms

    for i in range(retry):
        if is_open(ip, port):
            up = True
            break
        else:
            time.sleep(delay)
    return up


def traefik_routes_to_correct_backend(traefik_url, path, expected_port):
    """ Check if traefik followed the configuration and routed the
    request to the right backend """
    resp = requests.get(traefik_url + path)
    assert int(resp.text) == expected_port


def check_traefik_etcd_static_conf_ready(traefik_url):
    """ Allow traefik up to 10 sec to load its static configuration from the
    etcd cluster """
    timeout = time.time() + 10
    ready = False
    t = 0.1
    while not ready and time.time() < timeout:
        resp = requests.get(traefik_url + "/api/providers/etcdv3")
        ready = resp.status_code == 200
        if not ready:
            t = min(2, t * 2)
            time.sleep(t)
    assert ready  # Check that we got here because we are ready


def check_traefik_etcd_dynamic_conf_ready(traefik_url, expected_no_of_entries):
    """ Allow traefik up to 10 sec to load its dynamic configuration from the
    etcd cluster """
    timeout = time.time() + 10
    ready = False
    t = 0.05
    while not ready and time.time() < timeout:
        resp_backends = requests.get(traefik_url + "/api/providers/etcdv3/backends")
        resp_frontends = requests.get(traefik_url + "/api/providers/etcdv3/frontends")
        no_of_backend_entries = 0
        no_of_frontend_entries = 0
        if resp_backends.status_code == 200:
            no_of_backend_entries = len(resp_backends.json())
        if resp_frontends.status_code == 200:
            no_of_frontend_entries = len(resp_frontends.json())
        ready = (
            no_of_backend_entries == expected_no_of_entries
            and no_of_frontend_entries == expected_no_of_entries
        )
        if not ready:
            t = min(2, t * 2)
            time.sleep(t)
    assert ready  # Check that we got here because we are ready


def get_backend_ports():
    default_backend_port = get_port("default_backend")
    first_backend_port = get_port("first_backend")
    second_backend_port = get_port("second_backend")
    return default_backend_port, first_backend_port, second_backend_port


def check_backends_up():
    """ Verify if the backends started listening on their designated
    ports """
    default_backend_port, first_backend_port, second_backend_port = get_backend_ports()
    assert check_host_up("localhost", default_backend_port) == True
    assert check_host_up("localhost", first_backend_port) == True
    assert check_host_up("localhost", second_backend_port) == True


def check_traefik_up(traefik_port):
    """ Verify if traefik started listening on its designated port """
    assert check_host_up("localhost", traefik_port) == True


def check_routing(traefik_url):
    default_backend_port, first_backend_port, second_backend_port = get_backend_ports()
    """ Send GET requests for resources on different paths and check
    they are routed based on their path-prefixes """
    traefik_routes_to_correct_backend(traefik_url, "/otherthings", default_backend_port)
    traefik_routes_to_correct_backend(
        traefik_url, "/user/somebody", default_backend_port
    )
    traefik_routes_to_correct_backend(traefik_url, "/user/first", first_backend_port)
    traefik_routes_to_correct_backend(traefik_url, "/user/second", second_backend_port)
    traefik_routes_to_correct_backend(
        traefik_url, "/user/first/otherthings", first_backend_port
    )
    traefik_routes_to_correct_backend(
        traefik_url, "/user/second/otherthings", second_backend_port
    )
