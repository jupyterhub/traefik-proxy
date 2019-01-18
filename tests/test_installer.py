import pytest
import sys
import subprocess
import os

installer_module = "jupyterhub_traefik_proxy.install"


def cleanup(dirname):
    import shutil

    shutil.rmtree(dirname)


def assert_binaries_existence(deps_dir):
    traefik_bin = os.path.join(deps_dir, "traefik")
    etcd_bin = os.path.join(deps_dir, "etcd")
    etcdctl_bin = os.path.join(deps_dir, "etcdctl")

    assert os.path.exists(traefik_bin)
    assert os.path.exists(etcd_bin)
    assert os.path.exists(etcdctl_bin)


def test_default_conf():
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_deps_dir = os.path.join(parent_dir, "dependencies")

    try:
        subprocess.run([sys.executable, "-m", installer_module])
        assert os.path.exists(default_deps_dir)
        assert_binaries_existence(default_deps_dir)
    finally:
        cleanup(default_deps_dir)


def test_output_arg_new_dir(tmpdir):
    deps_dir = str(tmpdir.join("deps/out"))
    subprocess.run([sys.executable, "-m", installer_module, f"--output={deps_dir}"])

    assert os.path.exists(deps_dir)
    assert_binaries_existence(deps_dir)


def test_output_arg_existing_dir(tmpdir):
    deps_dir = tmpdir.mkdir("deps")
    subprocess.run([sys.executable, "-m", installer_module, f"--output={deps_dir}"])
    assert_binaries_existence(deps_dir)


def test_version(tmpdir):
    deps_dir = str(tmpdir.join("deps"))
    subprocess.run(
        [
            sys.executable,
            "-m",
            installer_module,
            f"--output={deps_dir}",
            "--traefik-version=1.7.0",
            "--etcd-version=3.2.25",
        ]
    )

    assert os.path.exists(deps_dir)
    assert_binaries_existence(deps_dir)


def test_linux_platform(tmpdir):
    deps_dir = str(tmpdir.join("deps"))
    subprocess.run(
        [
            sys.executable,
            "-m",
            installer_module,
            f"--output={deps_dir}",
            "--platform=linux-amd64",
        ]
    )

    assert os.path.exists(deps_dir)
    assert_binaries_existence(deps_dir)


def test_mac_platform(tmpdir):
    deps_dir = str(tmpdir.join("deps"))
    subprocess.run(
        [
            sys.executable,
            "-m",
            installer_module,
            f"--output={deps_dir}",
            "--platform=darwin-amd64",
        ]
    )

    assert os.path.exists(deps_dir)
    assert_binaries_existence(deps_dir)


def test_warning(tmpdir):
    deps_dir = str(tmpdir.join("deps"))
    output = subprocess.check_output(
        [
            sys.executable,
            "-m",
            installer_module,
            f"--output={deps_dir}",
            "--traefik-version=1.6.6",
            "--etcd-version=3.2.24",
        ],
        stderr=subprocess.STDOUT,
    )
    assert os.path.exists(deps_dir)
    assert_binaries_existence(deps_dir)
    assert output.decode().count("UserWarning") == 2
