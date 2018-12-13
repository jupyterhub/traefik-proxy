import sys
import os
from urllib.request import urlretrieve
import tarfile

plat = "linux-amd64"
traefik_version = "1.7.5"
etcd_version = "3.3.10"

DEPS_INSTALL_DIR_NAME = "dependencies"
HERE = os.path.abspath(os.path.dirname(__file__))


def install_traefik(prefix):
    traefik_dir = os.path.join(prefix, "traefik")
    traefik_bin = os.path.join(traefik_dir, "traefik")

    if os.path.exists(traefik_bin):
        print(f"Traefik {traefik_version} already exists")
        os.chmod(traefik_bin, 0o755)
        return

    traefik_url = (
        "https://github.com/containous/traefik/releases"
        f"/download/v{traefik_version}/traefik_{plat}"
    )
    if not os.path.exists(traefik_dir):
        print(f"Creating traefik installation directory")
        os.mkdir(traefik_dir)

    print(f"Downloading traefik {traefik_version}...")
    urlretrieve(traefik_url, traefik_bin)
    os.chmod(traefik_bin, 0o755)


def install_etcd(prefix):
    """Download and install the traefik binary"""
    etcd_dir = os.path.join(prefix, "etcd")
    etcd_arhive_name = os.path.join(etcd_dir, f"etcd-v{etcd_version}.tar.gz")
    etcd_bin = os.path.join(etcd_dir, f"etcd-v{etcd_version}-{plat}", "etcd")

    if os.path.exists(etcd_bin):
        print(f"Etcd {etcd_version} already exists")
        return

    etcd_url = (
        "https://github.com/etcd-io/etcd/releases/"
        f"/download/v{etcd_version}/etcd-v{etcd_version}-{plat}.tar.gz"
    )
    if not os.path.exists(etcd_dir):
        os.mkdir(etcd_dir)
    if not os.path.exists(etcd_arhive_name):
        print(f"Downloading etcd {etcd_version}...")
        urlretrieve(etcd_url, etcd_arhive_name)

    with (tarfile.open(etcd_arhive_name, "r")) as tar_ref:
        tar_ref.extractall(etcd_dir)


def main():
    deps_dir = os.path.join(HERE, DEPS_INSTALL_DIR_NAME)
    print(f"Creating dependencies directory {deps_dir}...")
    try:
        os.mkdir(deps_dir)
        print(f"Dependencies directory created.")
    except FileExistsError:
        print(f"Dependencies directory already exists.")

    install_traefik(deps_dir)
    install_etcd(deps_dir)


if __name__ == "__main__":
    main()
