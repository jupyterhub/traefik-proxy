import pytest
import sys
import subprocess
import os

installer_module = "jupyterhub_traefik_proxy.install"


def cleanup(dirname):
    import shutil

    shutil.rmtree(dirname)


def assert_binaries_existence(traefik_bin, etcd_bin, etcdctl_bin):
    assert os.path.exists(traefik_bin)
    assert os.path.exists(etcd_bin)
    assert os.path.exists(etcdctl_bin)


def construct_binaries_path(deps_dir):
    traefik_bin = os.path.join(deps_dir, "traefik")
    etcd_bin = os.path.join(deps_dir, "etcd")
    etcdctl_bin = os.path.join(deps_dir, "etcdctl")

    return traefik_bin, etcd_bin, etcdctl_bin


def test_default_conf():
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_deps_dir = os.path.join(parent_dir, "dependencies")
    traefik_bin, etcd_bin, etcdctl_bin = construct_binaries_path(default_deps_dir)

    subprocess.run([sys.executable, "-m", installer_module])

    assert os.path.exists(default_deps_dir)
    assert_binaries_existence(traefik_bin, etcd_bin, etcdctl_bin)

    cleanup(default_deps_dir)


def test_output_arg_new_dir():
    deps_dir = "./deps/out"
    traefik_bin, etcd_bin, etcdctl_bin = construct_binaries_path(deps_dir)

    subprocess.run([sys.executable, "-m", installer_module, f"--output={deps_dir}"])

    assert os.path.exists(deps_dir)
    assert_binaries_existence(traefik_bin, etcd_bin, etcdctl_bin)

    cleanup("./deps")


def test_output_arg_existing_dir():
    deps_dir = "./deps"
    os.mkdir(deps_dir)

    traefik_bin, etcd_bin, etcdctl_bin = construct_binaries_path(deps_dir)

    subprocess.run([sys.executable, "-m", installer_module, f"--output={deps_dir}"])

    assert_binaries_existence(traefik_bin, etcd_bin, etcdctl_bin)

    cleanup(deps_dir)


def test_version():
    deps_dir = "./deps"
    traefik_bin, etcd_bin, etcdctl_bin = construct_binaries_path(deps_dir)

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
    assert_binaries_existence(traefik_bin, etcd_bin, etcdctl_bin)

    cleanup("./deps")


def test_linux_platform():
    deps_dir = "./deps"
    traefik_bin, etcd_bin, etcdctl_bin = construct_binaries_path(deps_dir)

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
    assert_binaries_existence(traefik_bin, etcd_bin, etcdctl_bin)

    cleanup("./deps")


def test_mac_platform():
    deps_dir = "./deps"
    traefik_bin, etcd_bin, etcdctl_bin = construct_binaries_path(deps_dir)

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
    assert_binaries_existence(traefik_bin, etcd_bin, etcdctl_bin)

    cleanup("./deps")
