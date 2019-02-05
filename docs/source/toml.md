# Using traefik-proxy with TOML configuration files

**jupyterhub-traefik-proxy** can be used with simple toml configuration files, for smaller, single-node deployments such as 
[The Littlest JupyterHub](https://tljh.jupyter.org).

## How-To install TraefikTomlProxy
1. Install **traefik-proxy** throught the project’s [Github repository](https://github.com/jupyterhub/traefik-proxy)
2. Install **Jupyterhub**
3. Install **traefik**

* You can find the full installation guide and examples in the [Introduction section](install.md)

## How-To enable TraefikTomlProxy

You can enable JupyterHub to work with `TraefikTomlProxy` in jupyterhub_config.py, using the `proxy_class` configuration option.

You can choose to:

* use the `traefik_toml` entrypoint, e.g.:

    ```
    c.JupyterHub.proxy_class = "traefik_toml"
    ```

* use the class name, in which case, you have to import it, e.g.:

    ```
    from jupyterhub_traefik_proxy import TraefikTomlProxy
    c.JupyterHub.proxy_class = TraefikTomlProxy
    ```


## The toml configuration files

Traefik's configuration is divided into two parts:

* The **static** configuration (loaded only at the beginning)
* The **dynamic** configuration (can be hot-reloaded, without restarting the process).

Traefik allows us to have one file for the static configuration (the `traefik.toml`) and one or several files for the routes, that traefik would watch.


---
*   **Note**

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

Similary, you can override the dynamic configuration file by modifying the **toml_dynamic_config_file** argument:

```
c.TraefikTomlProxy.toml_dynamic_config_file="/path/to/dynamic_config_filename.toml"
```

---
*   **Note**

    **When JupyterHub starts the proxy**, it writes the static config once, then only edits the routes config file. 

    **When JupyterHub does not start the proxy**, the user is totally responsible for the static config and 
    JupyterHub is responsible exclusively for the routes.

---

## Externally managed TraefikTomlProxy
When TraefikTomlProxy is externally managed, service managers like [systemd](https://www.freedesktop.org/wiki/Software/systemd/) 
or [docker](https://www.docker.com/) will be responsible for starting and stopping the proxy.

In order to let JupyterHub know that the proxy will be managed externally, use the `should_start` configuration option:

```
c.TraefikTomlProxy.should_start = False
```

## Step-by-step example setup for [the-littlest-jupyterhub](https://github.com/jupyterhub/the-littlest-jupyterhub)

The Littlest JupyterHub (TLJH) is a simple JupyterHub distribution for a small (0-100) number of users on a single server.

In order to enable TraefikTomlProxy on TLJH, a minimal configuration is required.

1. Ensure **jupyterhub_config.py**

   JupyterHub configuration file, *jupyterhub_config.py* must specify at least:
   * that the proxy is externally managed
   * the traefik's api credentials
   * the dynamic configuration file, if different from *rules.toml* or if this file is located 
     in another place than traefik's default search directories (etc/traefik/, * $HOME/.traefik/, the working directory)

   Example configuration:
   ```
   from jupyterhub_traefik_proxy import TraefikTomlProxy

   # mark the proxy as externally managed
   c.TraefikTomlProxy.should_start = False
   # traefik api endpoint login password
   c.TraefikTomlProxy.traefik_api_password = "admin"
   # traefik api endpoint login username
   c.TraefikTomlProxy.traefik_api_username = "api_admin"
   # traefik's dynamic configuration file
   c.TraefikTomlProxy.toml_dynamic_config_file = "TLJH_INSTALL_DIR/rules.toml"
   # configure JupyterHub to use TraefikTomlProxy
   c.JupyterHub.proxy_class = TraefikTomlProxy
    ```

2. Ensure **traefik.toml**
   The static configuration file must configure at least:
   * the api entrypoint (and authenticate it)
   * websockets
   * the dynamic configuration file to watch

   Example configuration:
   ```
   [api]
   dashboard = true
   entrypoint = "auth_api"

   # TODO
   [entryPoints.auth_api]
   address = ":8099"

   [entryPoints.auth_api.auth.basic]
   users = [ "api_admin:$apr1$eS/j3kum$q/X2khsIEG/bBGsteP.x./",]

   [wss]
   protocol = "http"

   [file]
   filename = "./tests/rules.toml"
   watch = true
   ```

3. JupyterHub and the proxy are managed by *systemd* in TLJH. Make sure there is a a **unit configuration** file (*proxy*.service) 
for the proxy process to be supervised by systemd. 

   TLJH already uses traefik in order to enable HTTPS, so we can use the *traefik.service* unit configuration.
   Make sure you give traefik `rw` access to the dynamic configuration file and that this configuration file exists before the proxy is launched (it can be empty).

   * In *traefik.py*:

   ```
   # create an empty config file
   with open(os.path.join(state_dir, "rules.toml"), "w") as f:
           os.fchmod(f.fileno(), 0o600)
   ```

   * In *traefik.service*:

   ```
   # give rw access to the config file
   ReadWritePaths={install_prefix}/state/rules.toml
   ```


