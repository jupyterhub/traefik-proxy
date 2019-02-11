# Using traefik-proxy with TOML configuration files

**jupyterhub-traefik-proxy** can be used with simple toml configuration files, for smaller, single-node deployments such as 
[The Littlest JupyterHub](https://tljh.jupyter.org).

## How-To install TraefikTomlProxy

1. Install **traefik-proxy** through the project’s [GitHub repository](https://github.com/jupyterhub/traefik-proxy)
2. Install **Jupyterhub**
3. Install **traefik**

* You can find the full installation guide and examples in the [Introduction section](install.html#traefik-proxy-installation)

## How-To enable TraefikTomlProxy

You can enable JupyterHub to work with `TraefikTomlProxy` in jupyterhub_config.py, using the `proxy_class` configuration option.

You can choose to:

* use the `traefik_toml` entrypoint, new in JupyterHub 1.0, e.g.:

    ```
    c.JupyterHub.proxy_class = "traefik_toml"
    ```

* use the TraefikTomlProxy object, in which case, you have to import the module, e.g.:

    ```
    from jupyterhub_traefik_proxy import TraefikTomlProxy
    c.JupyterHub.proxy_class = TraefikTomlProxy
    ```


## Traefik configuration

Traefik's configuration is divided into two parts:

* The **static** configuration (loaded only at the beginning)
* The **dynamic** configuration (can be hot-reloaded, without restarting the proxy), 
where the routing table will be updated continuously.

Traefik allows us to have one file for the static configuration (the `traefik.toml`) and one or several files for the routes, that traefik would watch.

---
<span style="color:green">**Note !**</span>

**TraefikTomlProxy**, uses two configuration files: one file for the routes (**rules.toml**), and one for the static configuration (**traefik.toml**).

---

By **default**, Traefik will search for `traefik.toml` and `rules.toml` in the following places:

* /etc/traefik/
* $HOME/.traefik/
* . the working directory

You can override this in TraefikTomlProxy, by modifying the **toml_static_config_file** argument:

```
c.TraefikTomlProxy.toml_static_config_file="/path/to/static_config_filename.toml"
```

Similarly, you can override the dynamic configuration file by modifying the **toml_dynamic_config_file** argument:

```
c.TraefikTomlProxy.toml_dynamic_config_file="/path/to/dynamic_config_filename.toml"
```

---
<span style="color:green">**Note !**</span>

**When JupyterHub starts the proxy**, it writes the static config once, then only edits the routes config file. 

**When JupyterHub does not start the proxy**, the user is totally responsible for the static config and 
JupyterHub is responsible exclusively for the routes.
---

## Externally managed TraefikTomlProxy

When TraefikTomlProxy is externally managed, service managers like [systemd](https://www.freedesktop.org/wiki/Software/systemd/) 
or [docker](https://www.docker.com/) will be responsible for starting and stopping the proxy.

If TraefikTomlProxy is used as an externally managed service, then make sure you follow the steps enumerated below:

1. Let JupyterHub know that the proxy being used is TraefikTomlProxy, using the *proxy_class* configuration option:
    ```
    c.TraefikTomlProxy.proxy_class = "traefik_toml"
    ```

2. Configure `TraeficTomlProxy` in **jupyterhub_config.py**

   JupyterHub configuration file, *jupyterhub_config.py* must specify at least:
   * That the proxy is externally managed
   * The traefik api credentials
   * The dynamic configuration file, 
     if different from *rules.toml* or if this file is located 
     in another place than traefik's default search directories (etc/traefik/, $HOME/.traefik/, the working directory)

    Example configuration:
    ```
    # JupyterHub shouldn't start the proxy, it's already running
    c.TraefikTomlProxy.should_start = False

    # if not the default:
    c.TraefikTomlProxy.toml_dynamic_config_file = "somefile.toml"

    # traefik api credentials
    c.TraefikTomlProxy.traefik_api_username = "abc"
    c.TraefikTomlProxy.traefik_api_password = "xxx"
    ```

3. Ensure **traefik.toml**

   The static configuration file, *traefik.toml* must configure at least:
   * The default entrypoint
   * The api entrypoint (*and authenticate it*)
   * The websockets protocol
   * The dynamic configuration file to watch
    (*make sure this configuration file exists, even if empty before the proxy is launched*)

## Example setup
   
This is an example setup for using JupyterHub and TraefikTomlProxy managed by another service than Jupyterhub.

1. Configure the proxy through the JupyterHub configuration file, *jupyterhub_config.py*, e.g.:

   ```
   from jupyterhub_traefik_proxy import TraefikTomlProxy

   # mark the proxy as externally managed
   c.TraefikTomlProxy.should_start = False

   # traefik api endpoint login password
   c.TraefikTomlProxy.traefik_api_password = "admin"

   # traefik api endpoint login username
   c.TraefikTomlProxy.traefik_api_username = "api_admin"

   # traefik's dynamic configuration file
   c.TraefikTomlProxy.toml_dynamic_config_file = "path/to/rules.toml"

   # configure JupyterHub to use TraefikTomlProxy
   c.JupyterHub.proxy_class = TraefikTomlProxy
    ```

2. Create a traefik static configuration file, *traefik.toml*, e.g.:

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

    # the dynamic configuration file
    [file]
    filename = "rules.toml"
    watch = true
   ```

3. Start traefik with the configuration specified above, e.g.:
    ```
    $ traefik -c traefik.toml
    ```