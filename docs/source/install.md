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

3. In order to be able to launch JupyterHub with traefik-proxy or run the tests, **traefik**, **etcd** and **consul** must first be installed and added to your `PATH`.

   There are two ways you can install traefik, etcd and consul:

   1. Through traefik-proxy's **install utility**.

      ```
      $ python3 -m jupyterhub_traefik_proxy.install --traefik --etcd --consul --output=/usr/local/bin
      ```

      This will install the default versions of traefik, etcd and consul, namely `traefik-1.7.5`, `etcd-3.3.10` and `consul_1.5.0` to `/usr/local/bin` specified through the `--output` option.

      It is also possible to install the binaries individually. For example to install traefik only:

      ```
      $ python3 -m jupyterhub_traefik_proxy.install --traefik --output=/usr/local/bin
      ```

      If no directory is passed to the installer, a *dependencies* directory will be created in the `traefik-proxy` directory. In this case, you **must** add this directory to `PATH`, e.g.

      ```
      $ export PATH=$PATH:{$PWD}/dependencies
      ```

      If you want to install other versions of traefik, etcd and consul in a directory of your choice, just specify it to the installer through the following arguments:
        * `--traefik-version`
        * `--etcd-version`
        * `--consul-version`
        * `--output`

      Example:

      ```
      $ python3 -m jupyterhub_traefik_proxy.install --traefik --etcd --consul --output=dep \
               --traefik-version=1.6.6 --etcd-version=3.2.24 --consul-version=1.5.0
      ```

      If the desired install directory doesn't exist, it will be created by the installer.

      To get a list of all the available options:

      ```
      $ python3 -m jupyterhub_traefik_proxy.install --help
      ```

    2. From traefik, etcd and consul **release pages**:
       * Install [`traefik`](https://traefik.io/#easy-to-install)

       * Install [`etcd`](https://github.com/etcd-io/etcd/releases)

       * Install [`consul`](https://github.com/hashicorp/consul/releases)

## Enabling traefik-proxy in JupyterHub


[TraefikFileProviderProxy](https://github.com/jupyterhub/traefik-proxy/blob/HEAD/jupyterhub_traefik_proxy/fileprovider.py), [TraefikEtcdProxy](https://github.com/jupyterhub/traefik-proxy/blob/HEAD/jupyterhub_traefik_proxy/etcd.py) and [TraefikConsulProxy](https://github.com/jupyterhub/traefik-proxy/blob/HEAD/jupyterhub_traefik_proxy/consul.py)  are custom proxy implementations that subclass [Proxy](https://github.com/jupyterhub/jupyterhub/blob/HEAD/jupyterhub/proxy.py) and can register in JupyterHub config using `c.JupyterHub.proxy_class` entrypoint.

On startup, JupyterHub will look by default for a configuration file, *jupyterhub_config.py*, in the current working directory. If the configuration file is not in the current working directory,
you can load a specific config file and start JupyterHub using:

```
$ jupyterhub -f /path/to/jupyterhub_config.py
```

There is an example configuration file [here](https://github.com/jupyterhub/traefik-proxy/blob/HEAD/examples/jupyterhub_config.py) that configures JupyterHub to run with *TraefikEtcdProxy* as the proxy and uses dummyauthenticator and simplespawner to enable testing without administrative privileges.

In *jupyterhub_config.py*:

```
c.JupyterHub.proxy_class = "traefik_file"
# will configure JupyterHub to run with TraefikFileProviderProxy
```

```
c.JupyterHub.proxy_class = "traefik_etcd"
# will configure JupyterHub to run with TraefikEtcdProxy

```

```
c.JupyterHub.proxy_class = "traefik_consul"
# will configure JupyterHub to run with TraefikConsulProxy

```

## Implementation details

1. **Traefik Dashboard**

    Traefik provides a Web UI **dashboard** where you can see the frontends and backends registered, the routing rules, some metrics, but also other configuration elements. Find out more about traefik api's, [here](https://docs.traefik.io/configuration/api/#security).

    Because of **security** concerns, in traefik-proxy implementation, traefik api endpoint isn't exposed on the public http endpoint. Instead, it runs on a dedicated **authenticated endpoint** that's on localhost by default.

    The port on which traefik-proxy's api will run, as well as the username and password used for authenticating, can be passed to the proxy through `jupyterhub_config.py`, e.g.:

    ```
    c.TraefikFileProviderProxy.traefik_api_url = "http://127.0.0.1:8099"
    c.TraefikFileProviderProxy.traefik_api_password = "admin"
    c.TraefikFileProviderProxy.traefik_api_username = "admin"
    ```
    Check out TraefikProxy's **API Reference** for more configuration options.
    <br/><br/>
2. **TKvProxy class**

    TKvProxy is a JupyterHub Proxy implementation that uses traefik and a key-value store.
    **TraefikEtcdProxy** and **TraefikConsulProxy** are proxy implementations that sublass `TKvProxy`.
    Other custom proxies that wish to implementat a JupyterHub Trafik KV store Proxy can sublass `TKvProxy`.
    **TKvProxy** implements JupyterHub's Proxy public API and there is no need to override these public methods.
    The methods that **must be implemented** by the proxies that sublass `TKvProxy` are:
      * ***_define_kv_specific_static_config()***
        * Define the traefik static configuration that configures
          traefik's communication with the key-value store.
        * Will be called during startup if should_start is True.
        * Subclasses must define this method if the proxy is to be started by the Hub.
        * In order to be picked up by the proxy, the static configuration
          must be stored into `proxy.static_config` dict under the `kv_name` key.
      * ***_kv_atomic_add_route_parts(jupyterhub_routespec, target, data, route_keys, rule)***
        * Add the key-value pairs associated with a route within a key-value store transaction.
        * Will be called during add_route.
        * When retrieving or deleting a route, the parts of a route are expected to have the following structure:
          ```
          [ key: jupyterhub_routespec            , value: target ]
          [ key: target                          , value: data   ]
          [ key: route_keys.backend_url_path     , value: target ]
          [ key: route_keys.frontend_rule_path   , value: rule   ]
          [ key: route_keys.frontend_backend_path, value: route_keys.backend_alias]
          [ key: route_keys.backend_weight_path  , value: w(int) ]
          # where w is the weight of the backend to be used during load balancing)
          ```
        * Returns:
          * result (tuple):
              * The transaction status (int, 0: failure, positive: success)
              * The transaction response(str)
      * ***_kv_atomic_delete_route_parts(jupyterhub_routespec, route_keys)***
        * Delete the key-value pairs associated with a route, within a key-value store transaction (if the route exists).
        * Will be called during delete_route.
        * The keys associated with a route are:
          * jupyterhub_routespec
          * target
          * route_keys.backend_url_path
          * route_keys.frontend_rule_path
          * route_keys.frontend_backend_path
          * route_keys.backend_weight_path
        * Returns:
          * result (tuple):
            * The transaction status (int, 0: failure, positive: success)
            * The transaction response (str)
      * ***_kv_get_target(jupyterhub_routespec)***
        * Retrive the target from the key-value store.
        * The target is the value associated with `jupyterhub_routespec` key.
        * Returns:
          * The full URL associated with this route (str)
      * ***_kv_get_data(target)***
        * Retrive the data associated with the `target` from the key-value store.
        * Returns:
          * A JSONable dict that holds extra info about the route (dict)
      * ***_kv_get_route_parts(kv_entry)***
        * Retrive all the parts that make up a route (i.e. routespec, target, data) from the key-value store given a `kv_entry`.
        * A `kv_entry` is a key-value store entry where the key starts with `proxy.jupyterhub_prefix`. It is expected that only the routespecs
          will be prefixed with `proxy.jupyterhub_prefix` when added to the kv store.
        * Returns:
            * routespec: The normalized route specification passed in to add_route ([host]/path/)
            * target: The target host for this route (proto://host)
            * data: The arbitrary data dict that was passed in by JupyterHub when adding this route.
      * ***_kv_get_jupyterhub_prefixed_entries()***
        * Retrive from the kv store all the key-value pairs where the key starts with `proxy.jupyterhub_prefix`.
        * It is expected that only the routespecs will be prefixed with `proxy.jupyterhub_prefix` when added to the kv store.
        * Returns:
          * routes: A list of key-value store entries where the keys start with `proxy.jupyterhub_prefix`.

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
