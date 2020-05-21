# Enabling HTTPS

In order to protect the data and passwords transfered over the public network, you should not run JupyterHub without enabling **HTTPS**.

JupyterHub Traefik-Proxy supports **automatically** configuring HTTPS via [Let’s Encrypt](https://letsencrypt.org/docs/), or setting it
up **manually** with your own key and certificate.

## How-To HTTPS for JupyterHub managed Traefik-Proxy
1. Via **Let'Encrypt**:
    * Enable automatic https:
    ```python
    c.Proxy.traefik_auto_https=True
    ```
    * Set the email address used for Let's Encrypt registration:
    ```python
    c.Proxy.traefik_letsencrypt_email=""
    ```
    * Set the domain list:
    ```python
    c.Proxy.traefik_letsencrypt_domains=["jupyter.test"]
    ```
    * Set the the CA server to be used:
    ```python
    c.Proxy.traefik_acme_server="https://acme-v02.api.letsencrypt.org/directory"
    ```
    * Set the port to be used by Traefik for the Acme HTTP challenge:
    ```python
    # default port is 80
    c.Proxy.traefik_acme_challenge_port=8000
    ```
    <span style="color:green">**Note !**</span>

    **TraefikProxy**, supports only the most common challenge type, i.e. the [HTTP-01 ACME challenge](https://letsencrypt.org/docs/challenge-types/#http-01-challenge).
    If other challenge type is needed, one could setup the proxy to be externally managed to get access to all the Traefik's configuration options (including the
    ACME challenge type).

2. **Manually**, by providing your own key and certificate:

    Providing a certificate and key can be done by configuring JupyterHub to enable SSL encryption as specified in [the docs](https://jupyterhub.readthedocs.io/en/stable/getting-started/security-basics.html?highlight=https#enabling-ssl-encryption). Example:
    ```python
      c.JupyterHub.ssl_key = '/path/to/my.key'
      c.JupyterHub.ssl_cert = '/path/to/my.cert'
    ```

## How-To HTTPS for external Traefik-Proxy
If the proxy isn't managed by JupyterHub, HTTPS can be enabled through Traefik's static configuration file.
Checkout Traefik's documentation for [setting up ACME (Let's Encrypt) configuration](https://docs.traefik.io/v1.7/configuration/acme/)