import sys
import json

from os.path import abspath, dirname, join
from subprocess import Popen
from urllib.parse import urlparse
from tornado.httpclient import AsyncHTTPClient, HTTPRequest


async def check_traefik_dynamic_conf_ready(traefik_url, target):
    """ Check if traefik loaded its dynamic configuration from the
        etcd cluster """
    if traefik_url.endswith("/"):
        traefik_url = traefik_url[:-1]
    expected_backend = create_backend_alias_from_url(target)
    expected_frontend = create_frontend_alias_from_url(target)
    ready = False
    try:
        resp_backends = await AsyncHTTPClient().fetch(
            traefik_url + "/api/providers/etcdv3/backends"
        )
        resp_frontends = await AsyncHTTPClient().fetch(
            traefik_url + "/api/providers/etcdv3/frontends"
        )
        backends_data = json.loads(resp_backends.body)
        frontends_data = json.loads(resp_frontends.body)

        if resp_backends.code == 200 and resp_frontends.code == 200:
            ready = (
                expected_backend in backends_data
                and expected_frontend in frontends_data
            )
    except Exception as e:
        backends_rc, frontends_rc = e.response.code
        ready = False
    finally:
        return ready


async def check_traefik_static_conf_ready(traefik_url):
    """ Check if traefik loaded its static configuration from the
    etcd cluster """
    if traefik_url.endswith("/"):
        traefik_url = traefik_url[:-1]
    try:
        resp = await AsyncHTTPClient().fetch(traefik_url + "/api/providers/etcdv3")
        rc = resp.code
    except ConnectionRefusedError:
        rc = None
    except Exception as e:
        rc = e.response.code
    finally:
        return rc == 200


def launch_traefik_with_toml():
    config_file_path = abspath(join(dirname(__file__), "traefik.toml"))
    traefik = Popen(["traefik", "-c", config_file_path], stdout=None)
    return traefik


def launch_traefik_with_etcd():
    traefik = Popen(["traefik", "--etcd", "--etcd.useapiv3=true"], stdout=None)
    return traefik


def generate_traefik_toml():
    pass  # Not implemented


def create_backend_alias_from_url(url):
    target = urlparse(url)
    return "jupyterhub_backend_" + target.netloc


def create_frontend_alias_from_url(url):
    target = urlparse(url)
    return "jupyterhub_frontend_" + target.netloc


def create_backend_url_path(proxy, backend_alias):
    return (
        proxy.etcd_traefik_prefix + "backends/" + backend_alias + "/servers/server1/url"
    )


def create_backend_weight_path(proxy, backend_alias):
    return (
        proxy.etcd_traefik_prefix
        + "backends/"
        + backend_alias
        + "/servers/server1/weight"
    )


def create_frontend_backend_path(proxy, frontend_alias):
    return proxy.etcd_traefik_prefix + "frontends/" + frontend_alias + "/backend"


def create_frontend_rule_path(proxy, frontend_alias):
    return (
        proxy.etcd_traefik_prefix + "frontends/" + frontend_alias + "/routes/test/rule"
    )
