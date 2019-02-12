# jupyterhub-traefik-proxy

JupyterHub proxy implementation with traefik

### How to start JupyterHub with traefik-proxy using `jupyterhub_config.py`:

# 1. Install JupyterHub:

```
python3 -m pip install jupyterhub
```

Please visit [JupyterHub installation guide](https://jupyterhub.readthedocs.io/en/latest/installation-guide.html) for a complete installation guide.

# 2. Install traefik

Grab the latest binary for your platform from [traefik realeases page](https://github.com/containous/traefik/releases), e.g.

```
wget https://github.com/containous/traefik/releases/download/v1.7.0/traefik_linux-amd64
```
Mark the binary as executable, e.g.

```
chmod 755 traefik_linux-amd64
```
Add the traefik binary as `traefik`, and make sure it is on your PATH, e.g.

```
mv traefik_linux-amd64 /usr/local/bin/traefik
```

# 3. Install etcd

Download the latest archive for your platform from [etcd realeases page](https://github.com/etcd-io/etcd/releases), e.g.

```
wget https://github.com/etcd-io/etcd/releases/download/v3.3.10/etcd-v3.3.10-linux-amd64.tar.gz
```
Extract etcd and etcdctl executables from the archive, e.g.

```
tar xzvf etcd-v3.3.10-linux-amd64.tar.gz
```
Add etcd and etcdl to your PATH, e.g.

```
mv etcd /usr/local/bin/etcd
mv etcdctl /usr/local/bin/etcdctl
```

# 4. Start the etcd cluster, e.g.
```
etcd &> /dev/null &
```

# 5. Start JupyterHub:

```
jupyterhub --ip 127.0.0.1 --port=8000 -f ./examples/jupyterhub_config.py
```
Visit http://localhost:8000 in your browser, and sign in using any username and password.
