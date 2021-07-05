# Using TraefikFileProviderProxy

**jupyterhub-traefik-proxy** can be used with simple toml or yaml configuration files, for smaller, single-node deployments such as
[The Littlest JupyterHub](https://tljh.jupyter.org).

## How-To install TraefikFileProviderProxy

1. Install **jupyterhub**
2. Install **jupyterhub-traefik-proxy**
3. Install **traefik**

* You can find the full installation guide and examples in the [Introduction section](install.html#traefik-proxy-installation)

## How-To enable TraefikFileProviderProxy

You can enable JupyterHub to work with `TraefikFileProviderProxy` in jupyterhub_config.py, using the `proxy_class` configuration option.

You can choose to:

* use the `traefik_file` entrypoint, new in JupyterHub 1.0, e.g.:

    ```python
    c.JupyterHub.proxy_class = "traefik_file"
    ```

* use the TraefikFileProviderProxy object, in which case, you have to import the module, e.g.:

    ```python
    from jupyterhub_traefik_proxy import TraefikFileProviderProxy
    c.JupyterHub.proxy_class = TraefikFileProviderProxy
    ```


## Traefik configuration

Traefik's configuration is divided into two parts:

* The **static** configuration (loaded only at the beginning)
* The **dynamic** configuration (can be hot-reloaded, without restarting the proxy), 
where the routing table will be updated continuously.

Traefik allows us to have one file for the static configuration file (`traefik.toml` or `traefik.yaml`) and one or several files for the routes, that traefik would watch.

```{note}
  **TraefikFileProviderProxy**, uses two configuration files: one file for the routes (**rules.toml** or **rules.yaml**), and one for the static configuration (**traefik.toml** or **traefik.yaml**).
```


By **default**, Traefik will search for `traefik.toml` and `rules.toml` in the following places:

* /etc/traefik/
* $HOME/.traefik/
* . the working directory

You can override this in TraefikFileProviderProxy, by modifying the **toml_static_config_file** argument:

```python
c.TraefikFileProviderProxy.static_config_file="/path/to/static_config_filename.toml"
```

Similarly, you can override the dynamic configuration file by modifying the **dynamic_config_file** argument:

```python
c.TraefikFileProviderProxy.dynamic_config_file="/path/to/dynamic_config_filename.toml"
```

```{note}

* **When JupyterHub starts the proxy**, it writes the static config once, then only edits the dynamic config file. 

* **When JupyterHub does not start the proxy**, the user is totally responsible for the static config and 
JupyterHub is responsible exclusively for the routes.

* **When JupyterHub does not start the proxy**, the user should tell `traefik` to get its dynamic configuration
from a directory. Then, one (or more) dynamic configuration file(s) can be managed externally, and `dynamic_config_file`
will be managed by JupyterHub. This allows e.g., the administrator to configure traefik's API outside of JupyterHub.

```

## Externally managed TraefikFileProviderProxy

When TraefikFileProviderProxy is externally managed, service managers like [systemd](https://www.freedesktop.org/wiki/Software/systemd/) 
or [docker](https://www.docker.com/) will be responsible for starting and stopping the proxy.

If TraefikFileProviderProxy is used as an externally managed service, then make sure you follow the steps enumerated below:

1. Let JupyterHub know that the proxy being used is TraefikFileProviderProxy, using the *proxy_class* configuration option:
    ```python
    from jupyterhub_traefik_proxy import TraefikFileProviderProxy
    c.JupyterHub.proxy_class = TraefikFileProviderProxy
    ```

2. Configure `TraefikFileProviderProxy` in **jupyterhub_config.py**

   JupyterHub configuration file, *jupyterhub_config.py* must specify at least:
   * That the proxy is externally managed
   * The traefik api credentials
   * The dynamic configuration file, 
     if different from *rules.toml* or if this file is located 
     in another place than traefik's default search directories (etc/traefik/, $HOME/.traefik/, the working directory)

    Example configuration:
    ```python
    # JupyterHub shouldn't start the proxy, it's already running
    c.TraefikFileProviderProxy.should_start = False

    # if not the default:
    c.TraefikFileProviderProxy.dynamic_config_file = "/path/to/somefile.toml"

    # traefik api credentials
    c.TraefikFileProviderProxy.traefik_api_username = "abc"
    c.TraefikFileProviderProxy.traefik_api_password = "xxx"
    ```

3. Ensure **traefik.toml** / **traefik.yaml**

   The static configuration file, *traefik.toml* (or **traefik.yaml**) must configure at least:
   * The default entrypoint
   * The api entrypoint (*and authenticate it in a user-managed dynamic configuration file*)
   * The websockets protocol
   * The dynamic configuration directory to watch
    (*make sure this configuration directory exists, even if empty before the proxy is launched*)
   * Check `tests/config_files/traefik.toml` for an example.

## Example setup
   
This is an example setup for using JupyterHub and TraefikFileProviderProxy managed by another service than JupyterHub.

1. Configure the proxy through the JupyterHub configuration file, *jupyterhub_config.py*, e.g.:

   ```python
   from jupyterhub_traefik_proxy import TraefikFileProviderProxy

   # mark the proxy as externally managed
   c.TraefikFileProviderProxy.should_start = False

   # traefik api endpoint login password
   c.TraefikFileProviderProxy.traefik_api_password = "admin"

   # traefik api endpoint login username
   c.TraefikFileProviderProxy.traefik_api_username = "api_admin"

   # traefik's dynamic configuration file, which will be managed by JupyterHub
   c.TraefikFileProviderProxy.dynamic_config_file = "/var/run/traefik/rules.toml"

   # configure JupyterHub to use TraefikFileProviderProxy
   c.JupyterHub.proxy_class = TraefikFileProviderProxy
    ```

2. Create a traefik static configuration file, *traefik.toml*, e.g.:

    ```
    # the api entrypoint
    [api]
    dashboard = true

    # websockets protocol
    [wss]
    protocol = "http"

    # the port on localhost where traefik accepts http requests
    [entryPoints.web]
    address = ":8000"

    # the port on localhost where the traefik api and dashboard can be found
    [entryPoints.enter_api]
    address = ":8099"

    # the dynamic configuration directory
    # This must match the directory provided in Step 1. above.
    [providers.file]
    directory = "/var/run/traefik"
    watch = true
   ```

3. Create a traefik dynamic configuration file in the directory provided in the dynamic configuration above, to provide the api authentication parameters, e.g.

    ```
    # Router configuration for the api service
    [http.routers.router-api]
    rule = "Host(`localhost`) && PathPrefix(`/api`)"
    entryPoints = ["enter_api"]
    service = "api@internal"
    middlewares = ["auth_api"]

    # authenticate the traefik api entrypoint
    [http.middlewares.auth_api.basicAuth]
    users = [ "api_admin:$apr1$eS/j3kum$q/X2khsIEG/bBGsteP.x./",]
    ```

4. Start traefik with the configuration specified above, e.g.:
    ```bash
    $ traefik --configfile traefik.toml
    ```
