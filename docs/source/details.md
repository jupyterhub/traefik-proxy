# Implementation details

## Traefik API

traefik-proxy uses the [Traefik API](https://doc.traefik.io/traefik/operations/api/) to monitor routes and configurations.

Because of **security** concerns, in traefik-proxy implementation, traefik api endpoint isn't exposed on the public http endpoint. Instead, it runs on a dedicated **authenticated endpoint** that's on localhost by default.

The port on which traefik-proxy's api will run, as well as the username and password used for authenticating, can be passed to the proxy through `jupyterhub_config.py`, e.g.:

```python
c.TraefikFileProviderProxy.traefik_api_url = "http://127.0.0.1:8099"
c.TraefikFileProviderProxy.traefik_api_password = "admin"
c.TraefikFileProviderProxy.traefik_api_username = "admin"
```

Check out TraefikProxy's [API Reference](TraefikProxy) for more configuration options.

## Class structure

A JupyterHub Proxy implementation must implement these methods:

- `start` / `stop` (starting and stopping the proxy)
- `add_route`
- `delete_route`
- `get_all_routes`
- `get_route` (a default implementation is provided by the base class, based on get_all_routes)

Additionally, for traefik we need to set up the separate "static config" (API access and where routes will be stored) and "dynamic config" (the routing table itself, which changes as servers start and stop).
Where and how dynamic_config is stored is the ~only difference between TraefikProxy subclasses.

Setting up traefik configuration is in these methods:

- `_setup_traefik_static_config` - must be extended by subclasses to add any provider-specific configuration to `self.static_config`
- `_setup_traefik_dynamic_config` - usually not modified

TraefikProxy is organized into three levels:

First, is [](TraefikProxy). This class is responsible for everything traefik-specific.
It implements talking to the traefik API, and computing _what_ dynamic configuration is needed for each step.
This base class provides implementations of `start`, `stop`, `add_route`, `delete_route`, and `get_all_routes`.

TraefikProxy subclasses must implement _how_ dynamic config is stored, and set the appropriate static config to tell traefik how to load the dynamic config.
Specifically, the generic methods:

- `_setup_traefik_static_config` should extend `self.static_config` to configure the traefik [configuration discovery provider](https://doc.traefik.io/traefik/providers/overview/)
- `_apply_dynamic_config` stores a given dynamic config dictionary in the appropriate config store
- `_delete_dynamic_config` removes keys from the dynamic config store
- `_get_jupyterhub_dynamic_config` reads the whole jupyterhub part (not read by traefik itself)

We have two classes at this level:

- TraefikFileProviderProxy, which stores dynamic config in a toml or yaml file, and
- TKvProxy - another base class, which implements the above, based on a generic notion of a key-value store

TKvProxy is an adapter layer, implementing all of the above methods, based on a few basic actions on key-value stores:

- `_kv_atomic_set` should take a _flat dictionary_ of key _paths_ and string values, and store them.
- `_kv_atomic_delete` should delete a number of keys in a single transaction
- `_kv_get_tree` should recursively read everything in the key-value store under a prefix (returning the _flattened_ dictionary)

TKvProxy is responsible for translating between key-value-friendly "flat" dictionaries and the 'true' nested dictionary format of the configuration (i.e. the nested dictionary `{"a": {"b": 5}}` will be flattened to `{"a/b": "5"}`).

Finally, we have our specific key-value store implementations:

- [](TraefikRedisProxy)
- [](TraefikEtcdProxy)
- [](TraefikConsulProxy)

These classes only need to implement:

1. configuration necessary to connect to the key-value store
2. `_setup_traefik_static_config` to tell traefik how to talk to the key-value store
3. the above three `_kv_` methods for reading, writing, and deleting keys

## Testing jupyterhub-traefik-proxy

You can then run the all the test suite from the _traefik-proxy_ directory with:

```shell
pytest
```

Or you can run a specific test with:

```shell
pytest tests/<test-file-name>
```
