# Installation

## Traefik-proxy installation

1. Install **JupyterHub**:

   ```
   $ python3 -m pip install jupyterhub
   ```

2. Install **jupyterhub-traefik-proxy**:

   ```
   python3 -m pip install jupyterhub-traefik-proxy
   ```

3. In order to be able to launch JupyterHub with traefik-proxy or run the tests, **traefik**, must first be installed and added to your `PATH`.

   There are two ways you can install traefik:
   1. Through traefik-proxy's **install utility**.

      ```
      $ python3 -m jupyterhub_traefik_proxy.install --output=/usr/local/bin
      ```

      This will install `traefik`.

      This will install the default versions of traefik, to to `/usr/local/bin` specified through the `--output` option.

      If no directory is passed to the installer, a _dependencies_ directory will be created in the `traefik-proxy` directory. In this case, you **must** add this directory to `PATH`, e.g.

      ```
      $ export PATH=$PATH:{$PWD}/dependencies
      ```

      If you want to install other versions of traefik in a directory of your choice, just specify it to the installer through the following arguments:
      - `--traefik-version`
      - `--output`

      Example:

      ```
      $ python3 -m jupyterhub_traefik_proxy.install --output=dep \
               --traefik-version=2.4.8
      ```

      If the desired install directory doesn't exist, it will be created by the installer.

      To get a list of all the available options:

      ```
      $ python3 -m jupyterhub_traefik_proxy.install --help
      ```

   2. From traefik **release page**:
      - Install [`traefik`](https://doc.traefik.io/traefik/getting-started/install-traefik/)

## Installing a key-value store

If you want to use a key-value store to mediate configuration
(mainly for use in distributed deployments, such as containers),
you can get the key-value stores via their respective installation pages:

- Install [`redis`](https://redis.io/docs/install/install-redis/)

- Install [`etcd`](https://github.com/etcd-io/etcd/releases)

- Install [`consul`](https://github.com/hashicorp/consul/releases)

Or, more likely, select the appropriate container image.
You will also need to install a Python client for the Key-Value store of your choice:

- `redis`
- `etcdpy`
- `python-consul2`

Starting with jupyterhub-traefik-proxy 1.2, these can be installed via `extras`:

```shell
python3 -m pip install jupyterhub-traefik-proxy[redis]
# or [etcd] or [consul]
```

## Enabling traefik-proxy in JupyterHub

The `c.JupyterHub.proxy_class` option is how you tell JupyterHub to use a proxy implementation,
which are typically identified by strings.
You can import and assign the class, or more conveniently use the desired class's registration string, e.g. `traefik_redis` for TraefikRedisProxy.

On startup, JupyterHub will look by default for a configuration file, _jupyterhub_config.py_, in the current working directory. If the configuration file is not in the current working directory,
you can load a specific config file and start JupyterHub using:

```
$ jupyterhub -f /path/to/jupyterhub_config.py
```

There is an example configuration file [here](https://github.com/jupyterhub/traefik-proxy/blob/HEAD/examples/jupyterhub_config_redis.py) that configures JupyterHub to run with [TraefikRedisProxy](redis) as the proxy and uses dummyauthenticator and simplespawner to enable testing without administrative privileges.

In _jupyterhub_config.py_:

```python
c.JupyterHub.proxy_class = "traefik_file" # TraefikFileProviderProxy
# or
c.JupyterHub.proxy_class = "traefik_redis" # TraefikRedisProxy
# or
c.JupyterHub.proxy_class = "traefik_etcd" # TraefikEtcdProxy
# or
c.JupyterHub.proxy_class = "traefik_consul" # eTraefikConsulProxy
```
