import json
import os

import pytest

from jupyterhub_traefik_proxy import traefik_utils


# Mark all tests in this file as asyncio
def test_roundtrip_routes():
    pytest.mark.asyncio
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

    file_name = "test_roudtrip.toml"
    config_handler = traefik_utils.TraefikConfigFileHandler(file_name)
    config_handler.atomic_dump(routes)
    reloader = traefik_utils.TraefikConfigFileHandler(file_name)
    reloaded = reloader.load()
    os.remove(file_name)
    assert reloaded == routes


def test_atomic_writing(tmpdir):
    testfile = tmpdir.join("testfile")
    with testfile.open("w") as f:
        f.write("before")

    with traefik_utils.atomic_writing(str(testfile)) as f:
        f.write("after")

    # tempfile got cleaned up
    assert not os.path.exists(f.name)

    # file was updated
    with testfile.open("r") as f:
        assert f.read() == "after"

    # didn't leave any residue
    assert tmpdir.listdir() == [testfile]


def test_atomic_writing_recovery(tmpdir):
    testfile = tmpdir.join("testfile")
    with testfile.open("w") as f:
        f.write("before")

    with pytest.raises(TypeError):
        with traefik_utils.atomic_writing(str(testfile)) as f:
            f.write("after")
            f.write(b"invalid")

    # tempfile got cleaned up
    assert not os.path.exists(f.name)

    # file didn't get overwritten
    with testfile.open("r") as f:
        assert f.read() == "before"

    # didn't leave any residue
    assert tmpdir.listdir() == [testfile]
