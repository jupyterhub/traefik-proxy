from traitlets.config import Config

from jupyterhub_traefik_proxy.consul import TraefikConsulProxy
from jupyterhub_traefik_proxy.etcd import TraefikEtcdProxy
from jupyterhub_traefik_proxy.toml import TraefikTomlProxy


def test_toml_deprecation(caplog):
    cfg = Config()
    cfg.TraefikTomlProxy.toml_static_config_file = 'deprecated-static.toml'
    cfg.TraefikTomlProxy.toml_dynamic_config_file = 'deprecated-dynamic.toml'
    p = TraefikTomlProxy(config=cfg)
    assert p.static_config_file == 'deprecated-static.toml'

    assert p.dynamic_config_file == 'deprecated-dynamic.toml'

    log = '\n'.join([record.msg for record in caplog.records])
    assert 'TraefikFileProvider.dynamic_config_file instead' in log
    assert 'static_config_file instead' in log


def test_etcd_deprecation(caplog):
    cfg = Config()
    cfg.TraefikEtcdProxy.kv_url = "http://1.2.3.4:12345"
    cfg.TraefikEtcdProxy.kv_username = "user"
    cfg.TraefikEtcdProxy.kv_password = "pass"

    p = TraefikEtcdProxy(config=cfg)
    assert p.etcd_url == "http://1.2.3.4:12345"
    assert p.etcd_username == "user"
    assert p.etcd_password == "pass"

    log = '\n'.join([record.msg for record in caplog.records])
    assert 'TraefikEtcdProxy.etcd_url instead' in log
    assert 'TraefikEtcdProxy.etcd_username instead' in log
    assert 'TraefikEtcdProxy.etcd_password instead' in log


def test_consul_deprecation(caplog):
    cfg = Config()
    cfg.TraefikConsulProxy.kv_url = "http://1.2.3.4:12345"
    cfg.TraefikConsulProxy.kv_username = "user"
    cfg.TraefikConsulProxy.kv_password = "pass"

    p = TraefikConsulProxy(config=cfg)
    assert p.consul_url == "http://1.2.3.4:12345"
    assert p.consul_username == "user"
    assert p.consul_password == "pass"

    log = '\n'.join([record.msg for record in caplog.records])
    assert 'TraefikConsulProxy.consul_url instead' in log
    assert 'TraefikConsulProxy.consul_username instead' in log
    assert 'TraefikConsulProxy.consul_password instead' in log
