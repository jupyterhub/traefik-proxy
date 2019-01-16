import pytest
import json
import os
from jupyterhub_traefik_proxy import traefik_utils

# Mark all tests in this file as asyncio
def test_roundtrip_routes():
    pytestmark = pytest.mark.asyncio
    routes = {
        "backends": {
            "backend1": {
                "servers": {"server1": {"url": "http://127.0.0.1:9009", "weight": 1}}
            }
        },
        "frontends": {
            "frontend1": {
                "backend": "backend1",
                "passHostHeader": True,
                "routes": {
                    "test": {
                        "rule": "Host:host;PathPrefix:/proxy/path",
                        "data": json.dumps({"test": "test1"}),
                    }
                },
            }
        },
    }

    file = "test_roudtrip.toml"
    open(file, "a").close()
    traefik_utils.persist_routes(file, routes)
    reloaded = traefik_utils.load_routes(file)
    os.remove(file)
    assert reloaded == routes
