import sys
import json
import re

from os.path import abspath, dirname, join
from subprocess import Popen
from urllib.parse import urlparse
from tornado.httpclient import AsyncHTTPClient, HTTPRequest


async def check_traefik_dynamic_conf_ready(username, password, api_url, target, provider="etcdv3"):
    """ Check if traefik loaded its dynamic configuration from the
        etcd cluster """
    expected_backend = create_alias(target, "backend")
    expected_frontend = create_alias(target, "frontend")
    ready = False
    try:
        resp_backends = await AsyncHTTPClient().fetch(
            api_url + "/api/providers/" + provider + "/backends",
            auth_username=username,
            auth_password=password,
        )
        resp_frontends = await AsyncHTTPClient().fetch(
            api_url + "/api/providers/" + provider + "/frontends",
            auth_username=username,
            auth_password=password,
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


async def check_traefik_static_conf_ready(username, password, api_url, provider="etcdv3"):
    """ Check if traefik loaded its static configuration from the
    etcd cluster """
    try:
        resp = await AsyncHTTPClient().fetch(
            api_url + "/api/providers/" + provider,
            auth_username=username,
            auth_password=password,
        )
        rc = resp.code
    except ConnectionRefusedError:
        rc = None
    except Exception as e:
        rc = e.response.code
    finally:
        return rc == 200


def launch_traefik_with_toml():
    config_file_path = abspath(join(dirname(__file__), "../traefik.toml"))
    traefik = Popen(["traefik", "-c", config_file_path], stdout=None)
    return traefik


def launch_traefik_with_etcd():
    traefik = Popen(["traefik", "--etcd", "--etcd.useapiv3=true"], stdout=None)
    return traefik


def generate_traefik_toml():
    pass  # Not implemented


def replace_special_chars(string):
    return re.sub("[.:/]", "_", string)


def create_alias(url, server_type=""):
    return (
        server_type
        + replace_special_chars(urlparse(url).netloc)
    )


def create_backend_entry(proxy, backend_alias, separator="/", url=False, weight=False):
    backend_entry = ""
    if separator is "/":
        backend_entry = proxy.etcd_traefik_prefix
    backend_entry += (
        "backends"
        + separator
        + backend_alias
        + separator
        + "servers"
        + separator
        + "server1"
    )
    if url is True:
        backend_entry += separator + "url"
    elif weight is True:
        backend_entry += separator + "weight"

    return backend_entry


def create_frontend_backend_entry(proxy, frontend_alias):
    return proxy.etcd_traefik_prefix + "frontends/" + frontend_alias + "/backend"


def create_frontend_rule_entry(proxy, frontend_alias, separator="/"):
    frontend_rule_entry = ""
    if separator == "/":
        frontend_rule_entry = proxy.etcd_traefik_prefix
    frontend_rule_entry += (
        "frontends"
        + separator
        + frontend_alias
        + separator
        + "routes"
        + separator
        + "test"
        + separator
        + "rule"
    )

    return frontend_rule_entry
