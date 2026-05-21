"""sample jupyterhub config file for testing

configures jupyterhub to run with traefik_file.

configures jupyterhub with dummyauthenticator and simplespawner
to enable testing without administrative privileges.

requires jupyterhub 1.0
"""

c = get_config()  # noqa

c.JupyterHub.proxy_class = "traefik_file"
c.TraefikFileProviderProxy.traefik_api_username = "admin"
c.TraefikFileProviderProxy.traefik_api_password = "admin"
c.TraefikFileProviderProxy.traefik_log_level = "INFO"

c.TraefikProxy.enable_last_activity = True
c.TraefikProxy.last_activity_prometheus_url = "http://127.0.0.1:9090"
c.JupyterHub.log_level = "DEBUG"
# use dummy and simple auth/spawner for testing
c.JupyterHub.authenticator_class = "dummy"
c.JupyterHub.spawner_class = "simple"

# run notebooks in the current directory
from pathlib import Path

here = Path(__file__).absolute().parent
c.Spawner.notebook_dir = str(here)

# l
c.JupyterHub.cleanup_servers = False
# collect activity freqeuently for easier debugging
c.JupyterHub.last_activity_interval = 10
