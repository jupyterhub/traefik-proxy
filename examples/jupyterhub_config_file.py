"""sample jupyterhub config file for testing

configures jupyterhub to run with traefik_file.

configures jupyterhub with dummyauthenticator and simplespawner
to enable testing without administrative privileges.

requires jupyterhub 1.0.dev
"""

c.JupyterHub.proxy_class = "traefik_file"
c.TraefikFileProxy.traefik_api_username = "admin"
c.TraefikFileProxy.traefik_api_password = "admin"
c.TraefikFileProxy.traefik_log_level = "INFO"

# use dummy and simple auth/spawner for testing
c.JupyterHub.authenticator_class = "dummy"
c.JupyterHub.spawner_class = "simple"
