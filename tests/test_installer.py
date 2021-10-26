import pytest
import sys
import subprocess
import os

installer_module = "jupyterhub_traefik_proxy.install"

# Mark all tests in this file as slow
pytestmark = pytest.mark.slow


def cleanup(dirname):
    import shutil

    shutil.rmtree(dirname)


def assert_deps_dir_empty(deps_dir):
    assert os.path.exists(deps_dir)
    assert os.path.isdir(deps_dir)
    assert not os.listdir(deps_dir)


def assert_traefik_existence(deps_dir):
    traefik_bin = os.path.join(deps_dir, "traefik")
    assert os.path.exists(traefik_bin)

def test_default_conf():
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_deps_dir = os.path.join(parent_dir, "dependencies")

    subprocess.run([sys.executable, "-m", installer_module])
    assert not os.path.exists(default_deps_dir)


def test_install_only_traefik_default_version():
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_deps_dir = os.path.join(parent_dir, "dependencies")

    try:
        subprocess.run([sys.executable, "-m", installer_module, "--traefik"])
        assert_traefik_existence(default_deps_dir)
    finally:
        cleanup(default_deps_dir)


def test_install_all_binaries_default_version():
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_deps_dir = os.path.join(parent_dir, "dependencies")

    try:
        subprocess.run(
            [sys.executable, "-m", installer_module, "--traefik"]
        )
        assert_traefik_existence(default_deps_dir)
    finally:
        cleanup(default_deps_dir)


def test_output_arg_new_dir(tmpdir):
    deps_dir = str(tmpdir.join("deps/out"))
    subprocess.run(
        [sys.executable, "-m", installer_module, "--traefik", f"--output={deps_dir}"]
    )

    assert os.path.exists(deps_dir)
    assert_traefik_existence(deps_dir)


def test_output_arg_existing_dir(tmpdir):
    deps_dir = tmpdir.mkdir("deps")
    subprocess.run(
        [sys.executable, "-m", installer_module, "--traefik", f"--output={deps_dir}"]
    )
    assert_traefik_existence(deps_dir)


def test_version(tmpdir):
    deps_dir = str(tmpdir.join("deps"))
    subprocess.run(
        [
            sys.executable,
            "-m",
            installer_module,
            f"--output={deps_dir}",
            "--traefik",
            "--traefik-version=2.4.8",
        ]
    )

    assert os.path.exists(deps_dir)
    assert_traefik_existence(deps_dir)


def test_linux_arm_platform(tmpdir):
    deps_dir = str(tmpdir.join("deps"))
    subprocess.run(
        [
            sys.executable,
            "-m",
            installer_module,
            f"--output={deps_dir}",
            "--traefik",
            "--platform=linux-arm64",
        ]
    )

    assert os.path.exists(deps_dir)
    assert_traefik_existence(deps_dir)


def test_linux_amd64_platform(tmpdir):
    deps_dir = str(tmpdir.join("deps"))
    subprocess.run(
        [
            sys.executable,
            "-m",
            installer_module,
            f"--output={deps_dir}",
            "--traefik",
            "--platform=linux-amd64",
        ]
    )

    assert os.path.exists(deps_dir)
    assert_traefik_existence(deps_dir)


def test_mac_platform(tmpdir):
    deps_dir = str(tmpdir.join("deps"))
    subprocess.run(
        [
            sys.executable,
            "-m",
            installer_module,
            f"--output={deps_dir}",
            "--traefik",
            "--platform=darwin-amd64",
        ]
    )

    assert os.path.exists(deps_dir)
    assert_traefik_existence(deps_dir)


def test_warning(tmpdir):
    deps_dir = str(tmpdir.join("deps"))
    output = subprocess.check_output(
        [
            sys.executable,
            "-m",
            installer_module,
            f"--output={deps_dir}",
            "--traefik",
            "--traefik-version=2.4.1",
        ],
        stderr=subprocess.STDOUT,
    )
    assert os.path.exists(deps_dir)
    assert_traefik_existence(deps_dir)
    assert output.decode().count("UserWarning") == 1
