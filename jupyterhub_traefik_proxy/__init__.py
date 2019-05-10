"""Traefik implementation of the JupyterHub proxy API"""

from .proxy import TraefikProxy  # noqa
from .kv_proxy import TKvProxy  # noqa
from .etcd import TraefikEtcdProxy
from .consul import TraefikConsulProxy
from .toml import TraefikTomlProxy

from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions
