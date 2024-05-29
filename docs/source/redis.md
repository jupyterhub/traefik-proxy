# Using TraefikRedisProxy

[Redis](https://redis.io) is a distributed key-value store.
This should be the default choice when using jupyterhub-traefik-proxy
in a distributed setup, such as a Kubernetes cluster with multiple traefik instances.

## How-To install TraefikRedisProxy

1. Install **jupyterhub**
2. Install **jupyterhub-traefik-proxy** and [redis Python client](inv:redis:std#index)
   ```
   pip install jupyterhub-traefik-proxy[redis]
   ```
3. Install **traefik**
4. Install **Redis Server**

- You can find the full installation guide and examples in the [installation section](install)

## How-To enable TraefikRedisProxy

You can enable JupyterHub to work with `TraefikRedisProxy` in jupyterhub_config.py,
using the `proxy_class` configuration option:

```python
c.JupyterHub.proxy_class = "traefik_redis"
```

## Redis configuration

1. Depending on the value of the `should_start` proxy flag, you can choose whether or not JupyterHub will manage and start traefik itself.

   - When **should_start** is **True** (default), TraefikRedisProxy will generate the static configuration needed to connect to redis
     and store it in `traefik.toml` file.
     The traefik process will then be launched using this file.
   - When **should_start** is **False**, prior to starting the traefik process, you must create a _toml_ file with the desired
     traefik static configuration and pass it to traefik. Keep in mind that in order for the routes to be stored in **Redis**,
     this _toml_ file **must** specify redis as the provider.

2. TraefikRedisProxy searches in the redis key-value store for keys starting with the **kv_traefik_prefix** prefix to build its static configuration.

   Similarly, the dynamic configuration is built by searching for the **kv_jupyterhub_prefix**.

   ```{note}
   If you want to change or add to traefik's dynamic configuration options, you can add them to Redis under this prefix and traefik will pick them up.
   ```

   - The **default** values of these configuration options are:

     ```python
     kv_traefik_prefix = "/traefik/"
     kv_jupyterhub_prefix = "/jupyterhub/"
     ```

   - You can **override** the default values of the prefixes by passing their desired values through `jupyterhub_config.py` e.g.:
     ```python
     c.TraefikRedisProxy.kv_traefik_prefix = "/some_dynamic_config_prefix/"
     c.TraefikRedisProxy.kv_jupyterhub_prefix = "/some_other_config_prefix/"
     ```

3. By **default**, TraefikRedisProxy assumes Redis accepts client requests on the official **default** Redis port `6379` for client requests.

   ```python
   c.TraefikRedisProxy.redis_url = "redis://127.0.0.1:6379"
   ```

   If the Redis cluster is deployed differently than using the Redis defaults, then you **must** pass the Redis url to the proxy using
   the `redis_url` option in _jupyterhub_config.py_:

   ```python
   c.TraefikRedisProxy.redis_url = "redis://hostname:port"
   ```

:::{note}

**TraefikRedisProxy does not manage the Redis cluster** and assumes it is up and running before the proxy itself starts.

In order for traefik to reliably receive notifications of changes from redis, redis must enable [keyspace notifications](https://redis.io/docs/latest/develop/use/keyspace-notifications/),
e.g. with

```
--notify-keyspace-events KEA
```

To avoid losing configuration upon redis restart, the redis server should also enable persistence, e.g. with

```
--appendonly yes
```

:::

:::{note}

Based on how Redis is configured and started, TraefikRedisProxy needs to be told about some Redis configuration details, such as:

- Redis **address** where it accepts client requests
  ```python
  c.TraefikRedisProxy.redis_url="scheme://hostname:port"
  ```
- Redis **credentials** (if Redis has authentication enabled)
  ```python
  c.TraefikRedisProxy.redis_username="abc"
  c.TraefikRedisProxy.redis_password="123"
  ```
- Additional [redis client constructor](inv:redis:py:class#redis.Redis) options:
  ```python
  c.TraefikRedisProxy.redis_client_kwargs = {"retry_on_timeout": True}
  ```

:::

## Externally managed TraefikRedisProxy

If `traefik` is used as an externally managed service, then make sure you follow the steps enumerated below:

1. Let JupyterHub know that the proxy being used is TraefikRedisProxy, using the _proxy_class_ configuration option:

   ```python
   c.JupyterHub.proxy_class = "traefik_redis"
   ```

2. Configure `TraefikRedisProxy` in **jupyterhub_config.py**

   JupyterHub configuration file, _jupyterhub_config.py_ must specify at least:

   - That the proxy is externally managed
   - The traefik api credentials
   - The Redis credentials (if Redis authentication is enabled)

   Example configuration:

   ```python
   # JupyterHub shouldn't start the proxy, it's already running
   c.TraefikRedisProxy.should_start = False

   # if not the default:
   c.TraefikRedisProxy.redis_url = "redis://redis-host:2379"

   # traefik api credentials
   c.TraefikRedisProxy.traefik_api_username = "abc"
   c.TraefikRedisProxy.traefik_api_password = "123"

   # Redis credentials
   c.TraefikRedisProxy.redis_username = "def"
   c.TraefikRedisProxy.redis_password = "456"
   ```

3. Create a _toml_ file with traefik's desired static configuration

   Before starting the traefik process, you must create a _toml_ file with the desired
   traefik static configuration and pass it to traefik when you launch the process.
   Keep in mind that in order for the routes to be stored in **Redis**,
   this _toml_ file **must** specify Redis as the provider.

   - **Keep in mind that the static configuration must configure at least:**

     - The default entrypoint
     - The api entrypoint
     - The Redis provider

   - **Example:**

     ```toml
     [api]

     [entryPoints.http]
     address = "127.0.0.1:8000"

     [entryPoints.auth_api]
     address = "127.0.0.1:8099"

     [providers.redis]
     endpoints = [ "127.0.0.1:6379",]
     rootKey = "traefik"
     # username, password if needed
     username = "redisuser"
     password = "redispass"
     ```

## Example setup

This is an example setup for using JupyterHub and TraefikRedisProxy managed by another service than JupyterHub.

1. Configure the proxy through the JupyterHub configuration file, _jupyterhub_config.py_, e.g.:

   ```python
   # mark the proxy as externally managed
   c.TraefikRedisProxy.should_start = False

   # traefik api endpoint login password
   c.TraefikRedisProxy.traefik_api_password = "abc"

   # traefik api endpoint login username
   c.TraefikRedisProxy.traefik_api_username = "123"

   # Redis url where it accepts client requests
   c.TraefikRedisProxy.redis_url = "redis://127.0.0.1:6379"
   # username, password (if auth enabled)
   c.TraefikRedisProxy.redis_username = "def"
   c.TraefikRedisProxy.redis_password = "456"

   # configure JupyterHub to use TraefikRedisProxy
   c.JupyterHub.proxy_class = "traefik_redis"
   ```

2. Start a single-node Redis cluster on the default port on localhost. e.g.:

   ```bash
   redis-server

   # if redis-server isn't found on path, and you installed it with snap, you
   # probably need to do this:
   # export PATH="/snap/redis/current/usr/bin/:$PATH"
   ```

3. Create a traefik static configuration file, _traefik.toml_, e.g:.

   ```toml
   # enable the api
   [api]

   # the public port where traefik accepts http requests
   [entryPoints.http]
   address = ":8000"

   # the port on localhost where the traefik api should be found
   [entryPoints.auth_api]
   address = "localhost:8099"

   [providers.redis]
   # the Redis username, password (if auth is enabled)
   username = "def"
   password = "456"
   # the Redis address
   endpoints = ["127.0.0.1:2379"]
   # the prefix to use for the static configuration
   rootKey = "traefik"
   ```

4. Start traefik with the configuration specified above, e.g.:
   ```
   $ traefik -c traefik.toml
   ```
