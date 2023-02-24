import os
import subprocess
import sys

import pytest

installer_module = "jupyterhub_traefik_proxy.install"

# Mark all tests in this file as slow
pytestmark = pytest.mark.slow


def assert_only_traefik_existence(deps_dir):
    assert deps_dir.exists()
    assert os.listdir(deps_dir) == ["traefik"]


def test_default_conf(tmp_path):
    default_deps_dir = tmp_path / "dependencies"

    subprocess.run([sys.executable, "-m", installer_module], cwd=str(tmp_path))
    assert_only_traefik_existence(default_deps_dir)


def test_output_arg_new_dir(tmp_path):
    deps_dir = tmp_path / "deps" / "out"
    subprocess.run(
        [sys.executable, "-m", installer_module, "--traefik", f"--output={deps_dir}"]
    )
    assert_only_traefik_existence(deps_dir)


def test_output_arg_existing_dir(tmp_path):
    deps_dir = tmp_path / "deps"
    deps_dir.mkdir()
    subprocess.run(
        [sys.executable, "-m", installer_module, "--traefik", f"--output={deps_dir}"]
    )
    assert_only_traefik_existence(deps_dir)


def test_version(tmp_path):
    deps_dir = tmp_path / "deps"
    subprocess.run(
        [
            sys.executable,
            "-m",
            installer_module,
            f"--output={deps_dir}",
            "--traefik",
            "--traefik-version=2.8.8",
        ]
    )
    assert_only_traefik_existence(deps_dir)


@pytest.mark.parametrize(
    "platform",
    [
        "linux-amd64",
        "linux-arm64",
        "darwin-arm64",
        "darwin-amd64",
    ],
)
def test_platform(tmp_path, platform):
    deps_dir = tmp_path / "deps"
    subprocess.run(
        [
            sys.executable,
            "-m",
            installer_module,
            f"--output={deps_dir}",
            f"--platform={platform}",
        ]
    )
    assert_only_traefik_existence(deps_dir)
