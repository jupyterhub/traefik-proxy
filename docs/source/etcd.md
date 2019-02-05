# Using traefik-proxy with etcd

[Etcd](https://coreos.com/etcd/)
is a distributed key-value store.
This is the choice to use when using jupyterhub-traefik-proxy
in a distributed setup, such as a Kubernetes cluster,
e.g. with multiple traefik-proxy instances.

## How-To install TraefikEtcdProxy

1. Install **traefik-proxy** through the project’s [Github repository](https://github.com/jupyterhub/traefik-proxy)
2. Install **Jupyterhub**
3. Install **traefik**
4. Install **etcd**

* You can find the full installation guide and examples in the [Introduction section](install.html#traefik-proxy-installation)

## How-To enable TraefikEtcdProxy

You can enable JupyterHub to work with `TraefikEtcdProxy` in jupyterhub_config.py, 
using the `proxy_class` configuration option.

You can choose to:

* use the `traefik_etcd` entrypoint, e.g.:

    ```
    c.JupyterHub.proxy_class = "traefik_etcd"
    ```

* use the TraefikEtcdProxy object, in which case, you have to import the module, e.g.:

    ```
    from jupyterhub_traefik_proxy import TraefikEtcdProxy
    c.JupyterHub.proxy_class = TraefikEtcdProxy
    ```

## Etcd configuration

1. In order to use the TraefikEtcdProxy, prior to starting the traefik process, **etcd must** at least **contain traefik's static configuration**.

2. TraefikEtcdProxy searches the etcd key-value store after the **etcd_traefik_prefix** prefix for its static configuration. 
    Similarly, the dynamic configuration is searched after the **etcd_jupyterhub_prefix**.

    * The **default** values of this configurations options are:
        ```
        etcd_traefik_prefix = "/traefik/"
        etcd_jupyterhub_prefix = "/jupyterhub/"
        ```

    * You can **override** the default values of the prefixes by passing their desired values through `jupyterhub_config.py` e.g.:
        ```
        c.TraefikEtcdProxy.etcd_traefik_prefix="/some_static_config_prefix/"
        c.TraefikEtcdProxy.etcd_jupyterhub_prefix="/some_dynamic_config_prefix/"
        ```

3. By **default**, TraefikEtcdProxy assumes etcd accepts client requests on the official **default** etcd port `2379` for client requests.

    ```
    c.TraefikEtcdProxy.etcd_url="http://127.0.0.1:2379"
    ```

    If the etcd cluster is deployed differently than using the etcd defaults, then you **must** pass the etcd url to the proxy using 
    the `etcd_url` option in *jupyterhub_config.py*:

    ```
    c.TraefikEtcdProxy.etcd_url="scheme://hostname:port"
    ```

---
<span style="color:green">**Note 1**</span>

   **TraefikEtcdProxy does not manage the etcd cluster** and assumes it is up and running before the proxy itself starts.

   However, based on how etcd is configured and started, TraefikEtcdProxy needs to be told about 
   some etcd configuration details, such as:
   * etcd **address** where it accepts client requests
   * etcd **credentials** (TODO)

<span style="color:green">**Note 2**</span>

Etcd has two API versions: the API V3 and the API V2. Traefik suggests using Etcd API V3, 
because the API V2 won't be supported in the future.

---

Checkout the [etcd documentation](https://coreos.com/etcd/docs/latest/op-guide/configuration.html) 
to find out more about possible etcd configuration options.

## Externally managed TraefikEtcdProxy

If TraefikEtcdProxy is used as an externally managed service, then make sure you follow the steps enumerated below:

1. Let JupyterHub know that the proxy being used is TraefikEtcdProxy, using the *proxy_class* configuration option:
    ```
    c.TraefikEtcdProxy.proxy_class = traefik_etcd
    ```

2. Ensure **jupyterhub_config.py**

   JupyterHub configuration file, *jupyterhub_config.py* must specify at least:
   * That the proxy is externally managed
   * The traefik api credentials

3. Ensure etcd contains the traefik static configuration

   There are two ways to **add the static configuration to etcd**:
   * **Using [etcdctl](https://coreos.com/etcd/docs/latest/dev-guide/interacting_v3.html)**, a command line tool for interacting with etcd server.
      Because traefik suggests using the API V3 version of etcd, the API version must be set to version 3 via the ETCDCTL_API environment variable 
      before interacting with etcd, e.g.: 
      ```
      $ export ETCDCTL_API=3
      ```

      You must add the static configuration to etcd using key-value pairs, e.g.:
      ```
      $ etcdctl put key value
      ```

      ***Note**: The keys of the static configuration can be prefixed 
      with the value of the **etcd_traefik_prefix** if there is a need to retrieve them from the etcd store 
      by searching after this prefix, but it's not a must.*

   * **Using traefik [storeconfig](https://docs.traefik.io/user-guide/kv-config/#store-configuration-in-key-value-store) subcommand**
      This subcommand automates the process of uploading a toml configuration into the Key-value store without starting the traefik process.

      **Example:**

      Create a traefik.toml file with the desired static configuration, then use *storeconfig* to upload it to etcd.

      ```
      $ traefik storeconfig -c traefik.toml \
            --etcd \
            --etcd.endpoint=127.0.0.1:2379 \
            --etcd.useapiv3=true
     ```

   * **Keep in mind that the static configuration must configure at least:**
       * The default entrypoint
       * The api entrypoint (*and authenticate it*)
       * The websockets protocol
       * The etcd endpoint

## Example setup
   
This is an example setup for using JupyterHub and TraefikEtcdProxy managed by another service than Jupyterhub.

1. Configure the proxy through the JupyterHub configuration file, *jupyterhub_config.py*, e.g.:

   ```
   from jupyterhub_traefik_proxy import TraefikEtcdProxy

   # mark the proxy as externally managed
   c.TraefikEtcdProxy.should_start = False

   # traefik api endpoint login password
   c.TraefikEtcdProxy.traefik_api_password = "admin"

   # traefik api endpoint login username
   c.TraefikEtcdProxy.traefik_api_username = "api_admin"

   # etcd url where it accepts client requests
   c.TraefikEtcdProxy.etcd_url = "path/to/rules.toml"

   # configure JupyterHub to use TraefikEtcdProxy
   c.JupyterHub.proxy_class = TraefikEtcdProxy
    ```

2. Start a single-note etcd cluster on the default port on localhost. e.g.:
   ```
   $ etcd
   ```

3. Create a traefik static configuration file, *traefik.toml* and use *storeconfig* to add it to etcd.

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
    users = [ "api_admin:$apr1$eS/j3kum$q/X2khsIEG/bBGsteP.x./",]

    [etcd]
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
    $ traefik --etcd --etcd.useapiv3=true
    ```
