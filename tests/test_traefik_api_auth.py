"""Tests for the authentication to the traefik proxy api (dashboard)"""
import pytest
from jupyterhub.utils import exponential_backoff
from tornado.httpclient import AsyncHTTPClient

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    "username, password, expected_rc",
    [("api_admin", "admin", 200), ("api_admin", "1234", 401), ("", "", 401)],
)
async def test_traefik_api_auth(proxy, username, password, expected_rc):
    traefik_api_url = proxy.traefik_api_url + "/api/overview"

    async def api_login():
        try:
            if not username and not password:
                resp = await AsyncHTTPClient().fetch(traefik_api_url)
            else:
                resp = await AsyncHTTPClient().fetch(
                    traefik_api_url,
                    auth_username=username,
                    auth_password=password,
                )
        except ConnectionRefusedError:
            rc = None
        except Exception as e:
            rc = e.response.code
        else:
            rc = resp.code
        return rc

    async def cmp_api_login():
        rc = await api_login()
        if rc == expected_rc:
            return True
        else:
            print(f"{rc} != {expected_rc}")
            return False

    await exponential_backoff(cmp_api_login, "Traefik API not reacheable")

    rc = await api_login()
    assert rc == expected_rc
    return
