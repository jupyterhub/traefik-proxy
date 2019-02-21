# Installation


## Traefik-proxy installation

1. Install **JupyterHub**:
    ```
    $ python3 -m pip install jupyterhub
    ```

2. Install **jupyterhub-traefik-proxy**, which is available now as pre-release:

    ```
    python3 -m pip install jupyterhub-traefik-proxy
    ```

3. In order to be able to launch JupyterHub with traefik-proxy or run the tests, **traefik** and **etcd** must first be installed and added to your `PATH`.

   There are two ways you can install traefik and etcd:

   1. Through traefik-proxy's **install utility**.

      From `traefik-proxy` directory:

      ```
      $ python3 -m jupyterhub_traefik_proxy.install --output=/usr/local/bin
      ```
     
      This will install the default versions of traefik and etcd, namely `traefik-1.7.5` and `etcd-3.3.10` to `/usr/local/bin` specified through the `--output` option.

      If no directory is passed to the installer, a *dependencies* directory will be created in the `traefik-proxy` directory. In this case, you **must** add this directory to `PATH`, e.g.

      ```
      $ export PATH=$PATH:{$PWD}/dependencies
      ```

      If you want to install other versions of traefik and etcd in a directory of your choice, just specify it to the installer through the following arguments:
        * `--traefik-version`
        * `--etcd-version`
        * `--output`

      Example
      ```
      $ python3 -m jupyterhub_traefik_proxy.install --output=dep \
               --traefik-version=1.6.6 --etcd-version=3.2.24
      ```

      If the desired install directory doesn't exist, it will be created by the installer.

    2. From traefik and etcd **release pages**:
       * Install [`traefik`](https://traefik.io/#easy-to-install)

       * Install [`etcd`](https://traefik.io/#easy-to-install)

## Enabling traefik-proxy in JupyterHub


[TraefikEtcdProxy](https://github.com/jupyterhub/traefik-proxy/blob/master/jupyterhub_traefik_proxy/etcd.py) and [TraefikTomlProxy](https://github.com/jupyterhub/traefik-proxy/blob/master/jupyterhub_traefik_proxy/toml.py) are custom proxy implementations that subclass [Proxy](https://github.com/jupyterhub/jupyterhub/blob/master/jupyterhub/proxy.py) and can register in JupyterHub config using `c.JupyterHub.proxy_class` entrypoint.

On startup, JupyterHub will look by default for a configuration file, *jupyterhub_config.py*, in the current working directory. If the configuration file is not in the current working directory,
you can load a specific config file and start JupyterHub using:

```
$ jupyterhub -f /path/to/jupyterhub_config.py
```

There is an example configuration file [here](https://github.com/jupyterhub/traefik-proxy/blob/master/examples/jupyterhub_config.py) that configures JupyterHub to run with *TraefikEtcdProxy* as the proxy and uses dummyauthenticator and simplespawner to enable testing without administrative privileges.

In *jupyterhub_config.py*:

```
c.JupyterHub.proxy_class = "traefik_etcd"
# will configure JupyterHub to run with TraefikEtcdProxy

```

```
c.JupyterHub.proxy_class = "traefik_toml"
# will configure JupyterHub to run with TraefikTomlProxy
```

## Implementation details

Traefik provides a Web UI **dashboard** where you can see the frontends and backends registered, the routing rules, some metrics, but also other configuration elements. Find out more about traefik api's, [here](https://docs.traefik.io/configuration/api/#security).

Because of **security** concerns, in traefik-proxy implementation, traefik api endpoint isn't exposed on the public http endpoint. Instead, it runs on a dedicated **authenticated endpoint** that's on localhost by default.

The port on which traefik-proxy's api will run, as well as the username and password used for authenticating, can be passed to the proxy through `jupyterhub_config.py`, e.g.:

```
c.TraefikTomlProxy.traefik_api_url = "http://127.0.0.1:8099"
c.TraefikTomlProxy.traefik_api_password = "admin"
c.TraefikTomlProxy.traefik_api_username = "admin"
```

Check out TraefikProxy's **API Reference** for more configuration options.

## Testing jupyterhub-traefik-proxy

There are some tests that use *etcdctl* command line client for etcd.
Make sure to set environment variable ETCDCTL_API=3 before running the tests, so that the v3 API to be used, e.g.:

```
$ export ETCDCTL_API=3
```

You can then run the all the test suite from the *traefik-proxy* directory with:

```
$ pytest -v ./tests
```

Or you can run a specific test with:

```
$ pytest -v ./tests/<test-file-name>
```
