# Enabling HTTPS with TraefikProxy

When running JupyterHub, you almost always want to use TLS (HTTPS).
Traefik has a few ways to do that.
The first tricky bit is that traefik separates [dynamic configuration from static configuration](https://doc.traefik.io/traefik/getting-started/configuration-overview/#the-dynamic-configuration),
and some configuration needs to go in static, while some goes in dynamic.

## Static configuration

If you are using externally-managed traefik (`c.TraefikProxy.should_start = False`),
you must write the _static_ configuration file yourself.
The only static configuration required by juptyerhub-traefik-proxy
is the creation of the entrypoints for the api and jupyterhub itself:

```toml
# static configuration

# enable API
[api]

[entryPoints.auth_api]
address = "localhost:8099" # should match c.TraefikProxy.traefik_api_url

[entrypoints.https]
address = ":443"

[entrypoints.https.http.tls]
options = "default"
```

jupyterhub-traefik-proxy can take care of the rest because it will apply its dynamic configuration when JupyterHub starts.

## Manual SSL

Configuring SSL with your own certificates works the same with traefik proxy as any other JupyterHub proxy implementation:

```python
c.JupyterHub.ssl_cert = "/path/to/ssl.cert"
c.JupyterHub.ssl_key = "/path/to/ssl.key"
```

This will set the traefik **dynamic configuration**:

```toml
# dynamic configuration
[tls.stores.default.defaultCertificate]
certFile = "path/to/cert.crt"
keyFile  = "path/to/cert.key"
```

If you don't tell jupyterhub about these files,
you will need to set this configuration yourself in **dynamic configuration**
(Traefik ignores TLS configuration in the "static" configuration file).
Passing the certificates via JupyterHub configuration assumes the `options = "default"` static configuration:

```toml
# static configuration
[entrypoints.https.http.tls]
options = "default"
```

If you use your own static and dynamic configuration files, you don't have to use the 'default' TLS options or tell jupyterhub anything about your TLS configuration.

## Let's Encrypt

Traefik supports using Let's Encrypt for automatically issuing and renewing certificates.
It's great!

To configure traefik to use let's encrypt, first we need to register a [certificate resolver](https://doc.traefik.io/traefik/https/acme/) in static configuration:

```toml
# static configuration

# redirect all http requests to https
[entrypoints.httponly]
address = ":80"
[entryPoints.httponly.http.redirections.entryPoint]
to = "https"
scheme = "https"

# configure
[certificatesResolvers.letsencrypt.acme]
email = "you@example.com"
storage = "acme.json" # file where certificates are stored
# use the staging server to test your deployment
# uncomment this when you are ready for production
caServer = "https://acme-staging-v02.api.letsencrypt.org/directory"

# tlsChallenge means you don't need an http endpoint
[certificatesResolvers.letsencrypt.acme.tlsChallenge]
```

And in your extra dynamic configuration, specify the domain(s) you want certificates for:

```toml
# dynamic configuration
[tls.stores.default.defaultGeneratedCert]
resolver = "letsencrypt"
[tls.stores.default.defaultGeneratedCert.domain]
main = "hub.example.com"
sans = [
  # if you are serving more than one domain
  "other.service.example.com",
]
```

If you are using JupyterHub-managed traefik (`c.TraefikProxy.should_start = True`),
you can specify this same configuration via TraefikProxy's `extra_static_config` and `extra_dynamic_config`:

```python
c.TraefikProxy.traefik_entrypoint = "https"
c.TraefikProxy.extra_static_config = {
    "entryPoints": {
        "http": {
            "address": ":80"
        },
        "https": {
            "address": ":443",
            "http": {
                "tls": {
                    "options": "default"
                },
            },
        },
    },
    "certificatesResolvers": {
        "letsencrypt": {
            "acme": {
                "email": "you@example.com",
                "storage": "acme.json",
                "tlsChallenge": {},
            },
        },
    },
}


c.TraefikProxy.extra_dynamic_config = {
    "tls": {
        "stores": {
            "default": {
                "defaultGeneratedCert": {
                    "resolver": "letsencrypt",
                    "domain": {
                        "main": "hub.example.com",
                    },
                },
            },
        },
    },
}
```
