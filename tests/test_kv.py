import pytest

from jupyterhub_traefik_proxy.kv_proxy import TKvProxy


@pytest.mark.parametrize(
    "orig, expected",
    [
        ({}, {}),
        (
            {"key": "value"},
            {"key": "value"},
        ),
        (
            {"key": 1},
            {"key": "1"},
        ),
        (
            {"key": 1.5},
            {"key": "1.5"},
        ),
        (
            {"key": ["a", "b"]},
            {"key/0": "a", "key/1": "b"},
        ),
        (
            {"key": {"level": True, "deeper": {"anddeeper": False}}},
            {"key/level": "true", "key/deeper/anddeeper": "false"},
        ),
    ],
)
def test_flatten_dict(orig, expected):
    proxy = TKvProxy()
    flat = proxy.flatten_dict_for_kv(orig)
    assert flat == expected


@pytest.mark.parametrize(
    "orig, expected",
    [
        ({"key": object()}, ValueError),
    ],
)
def test_flatten_dict_error(orig, expected):
    proxy = TKvProxy()
    with pytest.raises(expected):
        proxy.flatten_dict_for_kv(orig)


@pytest.mark.parametrize(
    "flat, root_key, expected",
    [
        ([], "", {}),
        (
            [("key", "value")],
            "",
            {"key": "value"},
        ),
        (
            [("key", "value")],
            "nosuchkey",
            {},
        ),
        (
            [("key", "1")],
            "",
            {"key": "1"},
        ),
        (
            [("key/0", "a"), ("key/1", "b")],
            "",
            {"key": ["a", "b"]},
        ),
        (
            [("key/level", "true"), ("key/deeper/anddeeper", "false")],
            "",
            {"key": {"level": "true", "deeper": {"anddeeper": "false"}}},
        ),
        (
            [("key/level", "true"), ("key/deeper/anddeeper", "false")],
            "key/deeper",
            {"anddeeper": "false"},
        ),
    ],
)
def test_unflatten_dict(flat, root_key, expected):
    proxy = TKvProxy()
    unflat = proxy.unflatten_dict_from_kv(flat, root_key=root_key)
    assert unflat == expected


@pytest.mark.parametrize(
    "flat, expected",
    [
        (
            [("key/1", "value")],
            IndexError,
        ),
    ],
)
def test_unflatten_dict_error(flat, expected):
    proxy = TKvProxy()
    with pytest.raises(expected):
        proxy.unflatten_dict_from_kv(flat)
