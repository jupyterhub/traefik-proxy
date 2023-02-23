"""sample jupyterhub config file for testing

configures jupyterhub to run with traefik and etcd.

configures jupyterhub with dummyauthenticator and simplespawner
to enable testing without administrative privileges.

requires jupyterhub 1.0.dev
"""

c = get_config()  # noqa

c.JupyterHub.proxy_class = "traefik_etcd"
c.TraefikEtcdProxy.traefik_api_username = "admin"
c.TraefikEtcdProxy.traefik_api_password = "admin"

# use dummy and simple auth/spawner for testing
c.JupyterHub.authenticator_class = "dummy"
c.JupyterHub.spawner_class = "simple"
