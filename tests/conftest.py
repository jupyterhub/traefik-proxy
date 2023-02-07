"""General pytest fixtures"""

import os
import shutil
import subprocess
import sys
import time

import pytest
from _pytest.mark import Mark

from jupyterhub_traefik_proxy.etcd import TraefikEtcdProxy
from jupyterhub_traefik_proxy.consul import TraefikConsulProxy
from jupyterhub_traefik_proxy.fileprovider import TraefikFileProviderProxy

from jupyterhub.utils import exponential_backoff

from consul.aio import Consul

class Config:
    """Namespace for repeated variables.

    N.B. The user names and passwords are also stored in various configuration
    files, saved in ./tests/config_files, both in plain text, and in the case
    of the consul token, base64 encoded (so cannot be grep'ed)."""
    # Force etcdctl to run with the v3 API. This gives us access to various
    # commandss, e.g.  txn
    # Must be passed to the env parameter of any subprocess.Popen call that runs
    # etcdctl
    etcdctl_env = dict(os.environ, ETCDCTL_API="3")

    # Etcd3 auth login credentials
    etcd_password = "secret"
    etcd_user = "root"

    # Consol auth login credentials
    consul_token = "secret"

    # Traefik api auth login credentials
    traefik_api_user = "api_admin"
    traefik_api_pass = "admin"

    # The URL that should be proxied to jupyterhub
    # Putting here, can easily change between http and https
    public_url = "https://localhost:8000"

# Define a "slow" test marker so that we can run the slow tests at the end
# ref: https://docs.pytest.org/en/6.0.1/example/simple.html#control-skipping-of-tests-according-to-command-line-option
# ref: https://stackoverflow.com/questions/61533694/run-slow-pytest-commands-at-the-end-of-the-test-suite
empty_mark = Mark("", [], {})


def by_slow_marker(item):
    return item.get_closest_marker("slow", default=empty_mark)


def pytest_addoption(parser):
    parser.addoption("--slow-last", action="store_true", default=False)


def pytest_collection_modifyitems(items, config):
    if config.getoption("--slow-last"):
        items.sort(key=by_slow_marker)


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow.")


@pytest.fixture
async def no_auth_consul_proxy(request, launch_consul):
    """
    Fixture returning a configured TraefikConsulProxy.
    Consul acl disabled.
    """
    proxy = TraefikConsulProxy(
        public_url=Config.public_url,
        traefik_api_password=Config.traefik_api_pass,
        traefik_api_username=Config.traefik_api_user,
        check_route_timeout=45,
        should_start=True,
        log_level='DEBUG',
        traefik_log_level="DEBUG"
    )
    await proxy.start()
    yield proxy
    await proxy.stop()


@pytest.fixture
async def auth_consul_proxy(launch_consul_acl):
    """
    Fixture returning a configured TraefikConsulProxy.
    Consul acl enabled.
    """
    proxy = TraefikConsulProxy(
        public_url=Config.public_url,
        traefik_api_password=Config.traefik_api_pass,
        traefik_api_username=Config.traefik_api_user,
        kv_password=Config.consul_token,
        check_route_timeout=45,
        should_start=True,
        log_level='DEBUG'
    )
    await proxy.start()
    yield proxy
    await proxy.stop()


@pytest.fixture
async def no_auth_etcd_proxy(launch_etcd, wait_for_etcd):
    """
    Fixture returning a configured TraefikEtcdProxy.
    No etcd authentication.
    """
    proxy = TraefikEtcdProxy(
        public_url=Config.public_url,
        traefik_api_password=Config.traefik_api_pass,
        traefik_api_username=Config.traefik_api_user,
        check_route_timeout=45,
        should_start=True,
        log_level='DEBUG'
    )
    await proxy.start()
    yield proxy
    await proxy.stop()


@pytest.fixture
async def auth_etcd_proxy(launch_etcd_auth):
    """
    Fixture returning a configured TraefikEtcdProxy
    Etcd has credentials set up
    """
    proxy = TraefikEtcdProxy(
        public_url=Config.public_url,
        traefik_api_password=Config.traefik_api_pass,
        traefik_api_username=Config.traefik_api_user,
        kv_username="root",
        kv_password=Config.etcd_password,
        check_route_timeout=45,
        should_start=True,
        log_level='DEBUG'
    )
    await proxy.start()
    yield proxy
    await proxy.stop()


@pytest.fixture(params=["no_auth_etcd_proxy", "auth_etcd_proxy"])
def etcd_proxy(request):
    return request.getfixturevalue(request.param)


# There must be a way to parameterise this to run on both yaml and toml files?
@pytest.fixture
async def file_proxy_toml():
    """Fixture returning a configured TraefikFileProviderProxy"""
    dynamic_config_file = os.path.join(
        os.getcwd(), "tests", "config_files", "dynamic_config", "rules.toml"
    )
    static_config_file = "traefik.toml"
    proxy = _file_proxy(dynamic_config_file,
                        static_config_file=static_config_file,
                        should_start=True)
    await proxy.start()
    yield proxy
    await proxy.stop()

@pytest.fixture
async def file_proxy_yaml():
    dynamic_config_file = os.path.join(
        os.getcwd(), "tests", "config_files", "dynamic_config", "rules.yaml"
    )
    static_config_file = "traefik.yaml"
    proxy = _file_proxy(dynamic_config_file,
                        static_config_file=static_config_file,
                        should_start=True)
    await proxy.start()
    yield proxy
    await proxy.stop()

def _file_proxy(dynamic_config_file, **kwargs):
    ext = dynamic_config_file.rsplit('.', 1)[-1]
    static_config_file = os.path.join(
        os.getcwd(), f"traefik.{ext}"
    )
    return TraefikFileProviderProxy(
        public_url=Config.public_url,
        traefik_api_password=Config.traefik_api_pass,
        traefik_api_username=Config.traefik_api_user,
        dynamic_config_file = dynamic_config_file,
        check_route_timeout=60,
        log_level='DEBUG',
        **kwargs
    )

@pytest.fixture
async def external_file_proxy_yaml(launch_traefik_file):
    dynamic_config_file = os.path.join(
        os.getcwd(), "tests", "config_files", "dynamic_config", "rules.yaml"
    )
    proxy = _file_proxy(
        dynamic_config_file,
        should_start=False
    )
    await proxy._wait_for_static_config()
    yield proxy
    os.remove(dynamic_config_file)

@pytest.fixture
async def external_file_proxy_toml(launch_traefik_file):
    dynamic_config_file = os.path.join(
        os.getcwd(), "tests", "config_files", "dynamic_config", "rules.toml"
    )
    proxy = _file_proxy(
        dynamic_config_file,
        should_start=False
    )
    await proxy._wait_for_static_config()
    yield proxy
    os.remove(dynamic_config_file)


@pytest.fixture
async def external_consul_proxy(launch_consul, configure_consul, launch_traefik_consul):
    proxy = TraefikConsulProxy(
        public_url=Config.public_url,
        traefik_api_password=Config.traefik_api_pass,
        traefik_api_username=Config.traefik_api_user,
        check_route_timeout=45,
        should_start=False,
        log_level="DEBUG"
    )
    await proxy._wait_for_static_config()
    yield proxy


@pytest.fixture
async def auth_external_consul_proxy(launch_consul_acl, configure_consul_auth, launch_traefik_consul_auth):
    proxy = TraefikConsulProxy(
        public_url=Config.public_url,
        traefik_api_password=Config.traefik_api_pass,
        traefik_api_username=Config.traefik_api_user,
        kv_password=Config.consul_token,
        check_route_timeout=45,
        should_start=False,
        log_level="DEBUG"
    )
    await proxy._wait_for_static_config()
    yield proxy


@pytest.fixture
async def external_etcd_proxy(launch_etcd, configure_etcd, launch_traefik_etcd):
    proxy = TraefikEtcdProxy(
        public_url=Config.public_url,
        traefik_api_password=Config.traefik_api_pass,
        traefik_api_username=Config.traefik_api_user,
        check_route_timeout=45,
        should_start=False,
        log_level="DEBUG"
    )
    await proxy._wait_for_static_config()
    yield proxy
    proxy.kv_client.close()


@pytest.fixture
async def auth_external_etcd_proxy(launch_etcd_auth, configure_etcd_auth, launch_traefik_etcd_auth):
    proxy = TraefikEtcdProxy(
        public_url=Config.public_url,
        traefik_api_password=Config.traefik_api_pass,
        traefik_api_username=Config.traefik_api_user,
        kv_password=Config.etcd_password,
        kv_username="root",
        check_route_timeout=45,
        should_start=False,
        log_level="DEBUG"
    )
    await proxy._wait_for_static_config()
    yield proxy
    proxy.kv_client.close()


#########################################################################
# Fixtures for launching traefik, with each backend and with or without #
# authentication                                                        #
#########################################################################

@pytest.fixture
def launch_traefik_file():
    args = ("--configfile", "./tests/config_files/traefik.toml")
    print(f"\nLAUNCHING TRAEFIK with args: {args}\n")
    proc = _launch_traefik(*args)
    yield proc
    shutdown_traefik(proc)


@pytest.fixture
def launch_traefik_etcd():
    env = Config.etcdctl_env
    proc = _launch_traefik_cli("--providers.etcd", env=env)
    yield proc
    shutdown_traefik(proc)


@pytest.fixture
def launch_traefik_etcd_auth():
    extra_args = (
        "--providers.etcd.username=" + Config.etcd_user,
        "--providers.etcd.password=" + Config.etcd_password
    )
    proc = _launch_traefik_cli(*extra_args, env=Config.etcdctl_env)
    yield proc
    shutdown_traefik(proc)


@pytest.fixture
def launch_traefik_consul():
    proc = _launch_traefik_cli("--providers.consul")
    yield proc
    shutdown_traefik(proc)

@pytest.fixture
def launch_traefik_consul_auth():
    extra_args = (
        "--providers.consul.username=root",
        "--providers.consul.password=" + Config.consul_token
    )
    traefik_env = os.environ.copy()
    traefik_env.update({"CONSUL_HTTP_TOKEN": Config.consul_token})
    proc = _launch_traefik_cli(*extra_args, env=traefik_env)
    yield proc
    shutdown_traefik(proc)

def _launch_traefik_cli(*extra_args, env=None):
    default_args = (
        "--api",
        "--log.level=debug",
        "--entrypoints.web.address=:8000",
        "--entrypoints.enter_api.address=:8099"
    )
    args = default_args + extra_args
    return _launch_traefik(*args, env=env)

def _launch_traefik(*extra_args, env=None):
    traefik_launch_command = (
        "traefik",
    ) + extra_args
    proc = subprocess.Popen(traefik_launch_command, env=env)
    return proc

#########################################################################
# Fixtures for configuring the traefik providers                        #
#########################################################################

# Etcd Launchers and configurers #
##################################

@pytest.fixture
def configure_etcd(wait_for_etcd):
    """Load traefik api rules into the etcd kv store"""
    yield _config_etcd()

@pytest.fixture
def configure_etcd_auth():
    """Load traefik api rules into the etcd kv store, with authentication"""
    yield _config_etcd(
        "--user=" + Config.etcd_user + ":" + Config.etcd_password
        )

def _config_etcd(*extra_args):
    data_store_cmd = ("etcdctl", "txn") + extra_args
    # Load a pre-baked dynamic configuration into the etcd store.
    # This essentially puts authentication on the traefik api handler.
    with open('tests/config_files/traefik_etcd_txns.txt', 'r') as fd:
        txns = fd.read()
    proc = subprocess.Popen(data_store_cmd, stdin=subprocess.PIPE, env=Config.etcdctl_env)
    proc.communicate(txns.encode())
    proc.wait()

@pytest.fixture
def enable_auth_in_etcd():
    user = Config.etcd_user
    pw = Config.etcd_password
    subprocess.call(["etcdctl", "user", "add", f"{user}:{pw}"], env=Config.etcdctl_env)
    subprocess.call(["etcdctl", "user", "grant-role", "root", user], env=Config.etcdctl_env)
    assert (
        subprocess.check_output(["etcdctl", "auth", "enable"], env=Config.etcdctl_env)
        .decode(sys.stdout.encoding)
        .strip()
        == "Authentication Enabled"
    )
    yield

    assert (
        subprocess.check_output(
            ["etcdctl", "--user", f"{user}:{pw}", "auth", "disable"], env=Config.etcdctl_env
        ).decode(sys.stdout.encoding)
        .strip() == "Authentication Disabled"
    )
    subprocess.call(["etcdctl", "user", "revoke-role", "root", user], env=Config.etcdctl_env)
    subprocess.call(["etcdctl", "user", "delete", user], env=Config.etcdctl_env)


@pytest.fixture
def launch_etcd_auth(launch_etcd, wait_for_etcd, enable_auth_in_etcd):
    yield

@pytest.fixture()
def launch_etcd():
    etcd_proc = subprocess.Popen(["etcd", "--log-level=debug"])
    yield etcd_proc

    shutdown_etcd(etcd_proc)

@pytest.fixture
def wait_for_etcd():
    """Etcd may not be ready if we jump straight into the tests.
    Make sure it's running before we continue with configuring it or running
    tests against it.

    In production, etcd would already be running, so don't put this in the
    proxy classes.
    """
    import etcd3
    assert (
        "is healthy" in 
        subprocess.check_output(
            ["etcdctl", "endpoint", "health"],
            env=Config.etcdctl_env,
            stderr=subprocess.STDOUT
        ).decode(sys.stdout.encoding)
    )

#@pytest.fixture(scope="function", autouse=True)
# Is this referenced anywhere??
#@pytest.fixture
def clean_etcd():
    subprocess.run(["etcdctl", "del", '""', "--from-key=true"], env=Config.etcdctl_env)


# Consul Launchers and configurers #
####################################

@pytest.fixture
async def launch_consul():
    consul_proc = subprocess.Popen(
        ["consul", "agent", "-dev"]
    )
    await _wait_for_consul()
    yield consul_proc
    shutdown_consul(consul_proc)


@pytest.fixture
async def launch_consul_acl():
    consul_proc = subprocess.Popen([
            "consul",
            "agent",
            "-advertise=127.0.0.1",
            "-config-file=./tests/config_files/consul_config.json",
            "-bootstrap-expect=1",
        ]
    )

    await _wait_for_consul(token=Config.consul_token)
    yield consul_proc
    shutdown_consul(consul_proc, secret=Config.consul_token)
    shutil.rmtree(os.getcwd() + "/consul.data")


async def _wait_for_consul(token=None):
    """Consul takes ages to shutdown and start. Make sure it's running before
    we continue with configuring it or running tests against it.

    In production, consul would already be running, so don't put this in the
    proxy classes.
    """
    async def _check_consul():
        try:
            cli = Consul(token=token)
            index, data = await cli.kv.get('getting_any_nonexistent_key_will_do')
        except Exception as e:
            print(f"Consul not up: {e}")
            return False

        print( "Consul is up!" )
        return True

    await exponential_backoff(
        _check_consul,
        "Consul not available",
        timeout=20,
    )


@pytest.fixture
def configure_consul():
    """Load an initial config into the consul KV store"""
    yield _config_consul()


@pytest.fixture
def configure_consul_auth():
    """Load an initial config into the consul KV store, using authentication"""
    yield _config_consul(secret=Config.consul_token)


def _config_consul(secret=None):
    proc_env = None
    if secret is not None:
        proc_env = os.environ.copy()
        proc_env.update({"CONSUL_HTTP_TOKEN": secret})

    consul_import_cmd = [
        "consul", "kv", "import",
        "@tests/config_files/traefik_consul_config.json"
    ]

    """
    Try storing the static config to the kv store.
    Stop if the kv store isn't ready in 60s.
    """
    timeout = time.time() + 60
    while True:
        if time.time() > timeout:
            raise Exception("KV not ready! 60s timeout expired!")
        try:
            # Put static config from file in kv store.
            proc = subprocess.check_call(consul_import_cmd, env=proc_env)
            break
        except subprocess.CalledProcessError:
            time.sleep(3)

#########################################################################
# Teardown functions                                                    #
#########################################################################

def shutdown_consul(consul_proc, secret=None):
    # For some reason, without running `consul leave`, subsequent consul tests fail
    consul_env = None
    if secret is not None:
        consul_env = os.environ.copy()
        consul_env.update({"CONSUL_HTTP_TOKEN" : secret})
    subprocess.call(["consul", "leave"], env=consul_env)
    terminate_process(consul_proc, timeout=30)

def shutdown_etcd(etcd_proc):
    clean_etcd()
    terminate_process(etcd_proc, timeout=20)

    # There have been cases where default.etcd didn't exist...
    # Not sure why, but guess it doesn't really matter, just
    # check to be safe and remove it if there.
    default_etcd = os.path.join(os.getcwd(), "default.etcd")
    if os.path.exists(default_etcd):
        shutil.rmtree(default_etcd)

def shutdown_traefik(traefik_process):
    terminate_process(traefik_process)

def terminate_process(proc, timeout=5):
    proc.terminate()
    try:
        proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
    finally:
        proc.wait()

