import sys

from os.path import abspath, dirname, join
from subprocess import Popen
from urllib.parse import urlparse


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
