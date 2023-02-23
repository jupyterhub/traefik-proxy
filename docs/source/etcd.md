# Using TraefikEtcdProxy

[Etcd](https://coreos.com/etcd/)
is a distributed key-value store.
This and TraefikConsulProxy is the choice to use when using jupyterhub-traefik-proxy
in a distributed setup, such as a Kubernetes cluster,
e.g. with multiple traefik-proxy instances.

## How-To install TraefikEtcdProxy

3. Install **jupyterhub**
4. Install **jupyterhub-traefik-proxy**
5. Install **traefik**
6. Install **etcd**

- You can find the full installation guide and examples in the [Introduction section](install.html#traefik-proxy-installation)

## How-To enable TraefikEtcdProxy

You can enable JupyterHub to work with `TraefikEtcdProxy` in jupyterhub_config.py,
using the `proxy_class` configuration option.

You can choose to:

- use the `traefik_etcd` entrypoint, new in JupyterHub 1.0, e.g.:

  ```python
  c.JupyterHub.proxy_class = "traefik_etcd"
  ```

- use the TraefikEtcdProxy object, in which case, you have to import the module, e.g.:

  ```python
  from jupyterhub_traefik_proxy import TraefikEtcdProxy
  c.JupyterHub.proxy_class = TraefikEtcdProxy
  ```

## Etcd configuration

1. Depending on the value of the `should_start` proxy flag, you can choose whether or not TraefikEtcdProxy willl be externally managed.

   - When **should_start** is set to **True**, TraefikEtcdProxy will auto-generate its static configuration
     (using the override values or the defaults) and store it in `traefik.toml` file.
     The traefik process will then be launched using this file.
   - When **should_start** is set to **False**, prior to starting the traefik process, you must create a _toml_ file with the desired
     traefik static configuration and pass it to traefik. Keep in mind that in order for the routes to be stored in **etcd**,
     this _toml_ file **must** specify etcd as the provider.

2. TraefikEtcdProxy searches in the etcd key-value store the keys starting with the **kv_traefik_prefix** prefix in order to build its static configuration.

   Similarly, the dynamic configuration is built by searching the **kv_jupyterhub_prefix**.

   ```{note}
   If you want to change or add traefik's static configuration options, you can add them to etcd under this prefix and traefik will pick them up.
   ```

   - The **default** values of this configurations options are:

     ```python
     kv_traefik_prefix = "/traefik/"
     kv_jupyterhub_prefix = "/jupyterhub/"
     ```

   - You can **override** the default values of the prefixes by passing their desired values through `jupyterhub_config.py` e.g.:
     ```python
     c.TraefikEtcdProxy.kv_traefik_prefix = "/some_static_config_prefix/"
     c.TraefikEtcdProxy.kv_jupyterhub_prefix = "/some_dynamic_config_prefix/"
     ```

3. By **default**, TraefikEtcdProxy assumes etcd accepts client requests on the official **default** etcd port `2379` for client requests.

   ```python
   c.TraefikEtcdProxy.etcd_url = "http://127.0.0.1:2379"
   ```

   If the etcd cluster is deployed differently than using the etcd defaults, then you **must** pass the etcd url to the proxy using
   the `etcd_url` option in _jupyterhub_config.py_:

   ```python
   c.TraefikEtcdProxy.etcd_url = "scheme://hostname:port"
   ```

````{note}

1. **TraefikEtcdProxy does not manage the etcd cluster** and assumes it is up and running before the proxy itself starts.

   However, based on how etcd is configured and started, TraefikEtcdProxy needs to be told about
   some etcd configuration details, such as:
   * etcd **address** where it accepts client requests
     ```
     c.TraefikEtcdProxy.etcd_url="scheme://hostname:port"
     ```
   * etcd **credentials** (if etcd has authentication enabled)
     ```
     c.TraefikEtcdProxy.etcd_username="abc"
     c.TraefikEtcdProxy.etcd_password="123"
     ```

2. Etcd has two API versions: the API V3 and the API V2. Traefik suggests using Etcd API V3,
because the API V2 won't be supported in the future.

   Checkout the [etcd documentation](https://coreos.com/etcd/docs/latest/op-guide/configuration.html)
to find out more about possible etcd configuration options.
````

## Externally managed TraefikEtcdProxy

If TraefikEtcdProxy is used as an externally managed service, then make sure you follow the steps enumerated below:

1. Let JupyterHub know that the proxy being used is TraefikEtcdProxy, using the _proxy_class_ configuration option:

   ```python
   c.JupyterHub.proxy_class = "traefik_etcd"
   ```

2. Configure `TraefikEtcdProxy` in **jupyterhub_config.py**

   JupyterHub configuration file, _jupyterhub_config.py_ must specify at least:

   - That the proxy is externally managed
   - The traefik api credentials
   - The etcd credentials (if etcd authentication is enabled)

   Example configuration:

   ```python
   # JupyterHub shouldn't start the proxy, it's already running
   c.TraefikEtcdProxy.should_start = False

   # if not the default:
   c.TraefikEtcdProxy.etcd_url = "http://etcd-host:2379"

   # traefik api credentials
   c.TraefikEtcdProxy.traefik_api_username = "abc"
   c.TraefikEtcdProxy.traefik_api_password = "123"

   # etcd credentials
   c.TraefikEtcdProxy.etcd_username = "def"
   c.TraefikEtcdProxy.etcd_password = "456"
   ```

3. Create a _toml_ file with traefik's desired static configuration

   Before starting the traefik process, you must create a _toml_ file with the desired
   traefik static configuration and pass it to traefik when you launch the process.
   Keep in mind that in order for the routes to be stored in **etcd**,
   this _toml_ file **must** specify etcd as the provider/

   - **Keep in mind that the static configuration must configure at least:**

     - The default entrypoint
     - The api entrypoint (_and authenticate it_)
     - The websockets protocol
     - The etcd endpoint

   - **Example:**

     ```
      defaultentrypoints = ["http"]
      debug = true
      logLevel = "ERROR"

      [api]
      dashboard = true
      entrypoint = "auth_api"

      [wss]
      protocol = "http"

      [entryPoints.http]
      address = "127.0.0.1:8000"

      [entryPoints.auth_api]
      address = "127.0.0.1:8099"

      [entryPoints.auth_api.auth.basic]
      users = [ "abc:$apr1$eS/j3kum$q/X2khsIEG/bBGsteP.x./",]

      [etcd]
      endpoint = "127.0.0.1:2379"
      prefix = "/jupyterhub"
      useapiv3 = true
      watch = true
     ```

   ```{note}
     **If you choose to enable the authentication on etcd**, you can use this *toml* file to pass the credentials to traefik, e.g.:

         [etcd]
         username = "root"
         password = "admin"
         endpoint = "127.0.0.1:2379"
         ...
   ```

## Example setup

This is an example setup for using JupyterHub and TraefikEtcdProxy managed by another service than JupyterHub.

1. Configure the proxy through the JupyterHub configuration file, _jupyterhub_config.py_, e.g.:

   ```python
   from jupyterhub_traefik_proxy import TraefikEtcdProxy

   # mark the proxy as externally managed
   c.TraefikEtcdProxy.should_start = False

   # traefik api endpoint login password
   c.TraefikEtcdProxy.traefik_api_password = "abc"

   # traefik api endpoint login username
   c.TraefikEtcdProxy.traefik_api_username = "123"

   # etcd url where it accepts client requests
   c.TraefikEtcdProxy.etcd_url = "http://127.0.0.1:2379"

   # configure JupyterHub to use TraefikEtcdProxy
   c.JupyterHub.proxy_class = TraefikEtcdProxy
   ```

   ```{note}
    If you intend to enable authentication on etcd, add the etcd credentials to *jupyterhub_config.py*:

        # etcd username
        c.TraefikEtcdProxy.etcd_username = "def"
        # etcd password
        c.TraefikEtcdProxy.etcd_password = "456"
   ```

2. Start a single-note etcd cluster on the default port on localhost. e.g.:

   ```bash
   $ etcd
   ```

   ```{note}
    If you intend to enable authentication on etcd checkout
    [this guide](https://coreos.com/etcd/docs/latest/op-guide/authentication.html).
   ```

3. Create a traefik static configuration file, _traefik.toml_, e.g:.

   ```
   # the default entrypoint
   defaultentrypoints = ["http"]

   # the api entrypoint
   [api]
   dashboard = true
   entrypoint = "auth_api"

   # websockets protocol
   [wss]
   protocol = "http"

   # the port on localhost where traefik accepts http requests
   [entryPoints.http]
   address = ":8000"

   # the port on localhost where the traefik api and dashboard can be found
   [entryPoints.auth_api]
   address = ":8099"

   # authenticate the traefik api entrypoint
   [entryPoints.auth_api.auth.basic]
   users = [ "abc:$apr1$eS/j3kum$q/X2khsIEG/bBGsteP.x./",]

   [etcd]
   # the etcd username (if auth is enabled)
   username = "def"
   # the etcd password (if auth is enabled)
   password = "456"
   # the etcd address
   endpoint = "127.0.0.1:2379"
   # the prefix to use for the static configuration
   prefix = "/traefik/"
   # tell etcd to use the v3 version of the api
   useapiv3 = true
   # watch etcd for changes
   watch = true
   ```

4. Start traefik with the configuration specified above, e.g.:
   ```
   $ traefik -c traefik.toml
   ```
