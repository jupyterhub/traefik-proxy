"""sample jupyterhub config file for testing

configures jupyterhub to run with traefik_file.

configures jupyterhub with dummyauthenticator and simplespawner
to enable testing without administrative privileges.
"""

c = get_config()  # noqa

c.JupyterHub.proxy_class = "traefik_file"
c.TraefikFileProviderProxy.traefik_api_username = "admin"
c.TraefikFileProviderProxy.traefik_api_password = "admin"
c.TraefikFileProviderProxy.traefik_log_level = "INFO"

# use dummy and simple auth/spawner for testing
c.JupyterHub.authenticator_class = "dummy"
c.JupyterHub.spawner_class = "simple"
c.JupyterHub.ip = "127.0.0.1"
