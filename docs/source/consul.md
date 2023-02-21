# Using TraefikConsulProxy

[Consul](https://www.consul.io/)
is a distributed key-value store.
This and TraefikEtcdProxy is the choice to use when using jupyterhub-traefik-proxy
in a distributed setup, such as a Kubernetes cluster,
e.g. with multiple traefik-proxy instances.

## How-To install TraefikConsulProxy

3. Install **jupyterhub**
2. Install **jupyterhub-traefik-proxy**
3. Install **traefik**
4. Install **consul**

* You can find the full installation guide and examples in the [Introduction section](install.html#traefik-proxy-installation)

## How-To enable TraefikConsulProxy

You can enable JupyterHub to work with `TraefikConsulProxy` in jupyterhub_config.py,
using the `proxy_class` configuration option.

You can choose to:

* use the `traefik_consul` entrypoint, new in JupyterHub 1.0, e.g.:

    ```python
    c.JupyterHub.proxy_class = "traefik_consul"
    ```

* use the TraefikConsulProxy object, in which case, you have to import the module, e.g.:

    ```python
    from jupyterhub_traefik_proxy import TraefikConsulProxy
    c.JupyterHub.proxy_class = TraefikConsulProxy
    ```

## Consul configuration

1. Depending on the value of the ```should_start``` proxy flag, you can choose whether or not TraefikConsulProxy willl be externally managed.

   * When **should_start** is set to **True**, TraefikConsulProxy will auto-generate its static configuration
     (using the override values or the defaults) and store it in ```traefik.toml``` file.
     The traefik process will then be launched using this file.
   * When **should_start** is set to **False**, prior to starting the traefik process, you must create a *toml* file with the desired
     traefik static configuration and pass it to traefik. Keep in mind that in order for the routes to be stored in **consul**,
     this *toml* file **must** specify consul as the provider.

2. TraefikConsulProxy searches in the consul key-value store the keys starting with the **kv_traefik_prefix** prefix in order to build its static configuration.

   Similarly, the dynamic configuration is built by searching the **kv_jupyterhub_prefix**.

   ```{note}
    If you want to change or add traefik's static configuration options, you can add them to consul under this prefix and traefik will pick them up.
   ```

    * The **default** values of this configurations options are:
        ```
        kv_traefik_prefix = "traefik/"
        kv_jupyterhub_prefix = "jupyterhub/"
        ```

    * You can **override** the default values of the prefixes by passing their desired values through `jupyterhub_config.py` e.g.:
        ```
        c.TraefikConsulProxy.kv_traefik_prefix="some_static_config_prefix/"
        c.TraefikConsulProxy.kv_jupyterhub_prefix="some_dynamic_config_prefix/"
        ```

3. By **default**, TraefikConsulProxy assumes consul accepts client requests on the official **default** consul port `8500` for client requests.

    ```python
    c.TraefikConsulProxy.consul_url = "http://127.0.0.1:8500"
    ```

    If the consul cluster is deployed differently than using the consul defaults, then you **must** pass the consul url to the proxy using
    the `consul_url` option in *jupyterhub_config.py*:

    ```python
    c.TraefikConsulProxy.consul_url = "scheme://hostname:port"
    ```

    ```{note}
    **TraefikConsulProxy does not manage the consul cluster** and assumes it is up and running before the proxy itself starts.
    However, based on how consul is configured and started, TraefikConsulProxy needs to be told about
    some consul configuration details, such as:
      * consul **address** where it accepts client requests
        ```python
        c.TraefikConsulProxy.consul_url = "scheme://hostname:port"
        ```
      * consul **credentials** (if consul has acl enabled)
        ```pythno
          c.TraefikConsulProxy.consul_password = "123"
        ```

    Checkout the [consul documentation](https://learn.hashicorp.com/consul/)
    to find out more about possible consul configuration options.
    ```

## Externally managed TraefikConsulProxy

If TraefikConsulProxy is used as an externally managed service, then make sure you follow the steps enumerated below:

1. Let JupyterHub know that the proxy being used is TraefikConsulProxy, using the *proxy_class* configuration option:
    ```python
    c.JupyterHub.proxy_class = "traefik_consul"
    ```

2. Configure `TraefikConsulProxy` in **jupyterhub_config.py**

   JupyterHub configuration file, *jupyterhub_config.py* must specify at least:
   * That the proxy is externally managed
   * The traefik api credentials
   * The consul credentials (if consul acl is enabled)

   Example configuration:
   ```python
   # JupyterHub shouldn't start the proxy, it's already running
   c.TraefikConsulProxy.should_start = False

   # if not the default:
   c.TraefikConsulProxy.consul_url = "http://consul-host:2379"

   # traefik api credentials
   c.TraefikConsulProxy.traefik_api_username = "abc"
   c.TraefikConsulProxy.traefik_api_password = "123"

   # consul acl token
   c.TraefikConsulProxy.consul_password = "456"
   ```

3. Create a *toml* file with traefik's desired static configuration

   Before starting the traefik process, you must create a *toml* file with the desired
   traefik static configuration and pass it to traefik when you launch the process.
   Keep in mind that in order for the routes to be stored in **consul**,
   this *toml* file **must** specify consul as the provider/

   * **Keep in mind that the static configuration must configure at least:**
       * The default entrypoint
       * The api entrypoint (*and authenticate it*)
       * The websockets protocol
       * The consul endpoint

    Example:

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

      [consul]
      endpoint = "127.0.0.1:8500"
      prefix = "traefik/"
      watch = true
     ```

     ```{note}
     If you choose to enable consul Access Control Lists (ACLs) to secure the UI, API, CLI, service communications, and agent communications, you can use this *toml* file to pass the credentials to traefik, e.g.:
        ```
          [consul]
          password = "admin"
          ...
        ```
     ```

## Example setup

This is an example setup for using JupyterHub and TraefikConsulProxy managed by another service than JupyterHub.

1. Configure the proxy through the JupyterHub configuration file, *jupyterhub_config.py*, e.g.:

   ```python
   from jupyterhub_traefik_proxy import TraefikConsulProxy

   # mark the proxy as externally managed
   c.TraefikConsulProxy.should_start = False

   # traefik api endpoint login password
   c.TraefikConsulProxy.traefik_api_password = "abc"

   # traefik api endpoint login username
   c.TraefikConsulProxy.traefik_api_username = "123"

   # consul url where it accepts client requests
   c.TraefikConsulProxy.consul_url = "path/to/rules.toml"

   # configure JupyterHub to use TraefikConsulProxy
   c.JupyterHub.proxy_class = TraefikConsulProxy
   ```

    ```{note}
    If you intend to enable consul acl, add the acl token to *jupyterhub_config.py* under *consul_password*:

        # consul token
        c.TraefikConsulProxy.consul_password = "456"
    ```

2. Starts the agent in development mode on the default port on localhost. e.g.:
   ```bash
   $ consul agent -dev
   ```

   ```{note}
    If you intend to enable consul acl, checkout [this guide](https://learn.hashicorp.com/consul/security-networking/production-acls).
   ```

3. Create a traefik static configuration file, *traefik.toml*, e.g:.

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

    [consul]
    # the consul acl token (if acl is enabled)
    password = "456"
    # the consul address
    endpoint = "127.0.0.1:8500"
    # the prefix to use for the static configuration
    prefix = "traefik/"
    # watch consul for changes
    watch = true
   ```

4. Start traefik with the configuration specified above, e.g.:
    ```bash
    $ traefik -c traefik.toml
    ```
