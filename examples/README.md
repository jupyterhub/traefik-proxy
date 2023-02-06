# JupyterHub configuration examples

Steps to follow when using a configuration example:

1. install jupyterhub, e.g.:
    ```
    $ python3 -m pip install jupyterhub
    ```

2. install traefik and etcd, e.g.:
    ```
    $ python3 -m jupyterhub_traefik_proxy.install --output=/usr/local/bin
    ```

3. if you're using the configuration example for traefik_etcd, start etcd, e.g.:
    ```
    $ etcd
    ```

4. start jupyterhub using a configuration example, e.g.:
    ```
    jupyterhub --ip 127.0.0.1 --port=8000 -f ./examples/jupyterhub_config_etcd.py
    ```
    Visit http://localhost:8000 in your browser, and sign in using any username and password.
