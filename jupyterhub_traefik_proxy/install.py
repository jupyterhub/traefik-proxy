import sys
import os
from urllib.request import urlretrieve
import tarfile
import argparse
import textwrap

HERE = os.path.abspath(os.path.dirname(__file__))


def install_traefik(prefix, plat, traefik_version):
    traefik_dir = os.path.join(prefix, "traefik")
    traefik_version_dir = os.path.join(
        traefik_dir, f"traefik-v{traefik_version}-{plat}"
    )
    traefik_bin = os.path.join(traefik_version_dir, "traefik")

    if os.path.exists(traefik_bin):
        print(f"Traefik {traefik_version} already exists")
        os.chmod(traefik_bin, 0o755)
        print("--- Done ---")
        return

    traefik_url = (
        "https://github.com/containous/traefik/releases"
        f"/download/v{traefik_version}/traefik_{plat}"
    )
    if not os.path.exists(traefik_dir):
        print(f"Creating traefik directory {traefik_dir}...")
        os.mkdir(traefik_dir)
    else:
        print(f"Directory {traefik_dir} already exists")

    if not os.path.exists(traefik_version_dir):
        print(f"Creating directory {traefik_version_dir}...")
        os.mkdir(traefik_version_dir)
    else:
        print(f"Directory {traefik_version_dir} already exists")

    print(f"Downloading traefik {traefik_version}...")
    urlretrieve(traefik_url, traefik_bin)
    os.chmod(traefik_bin, 0o755)

    print("--- Done ---")


def install_etcd(prefix, plat, etcd_version):
    """Download and install the traefik binary"""
    etcd_dir = os.path.join(prefix, "etcd")
    etcd_arhive_name = os.path.join(etcd_dir, f"etcd-v{etcd_version}.tar.gz")
    etcd_bin = os.path.join(etcd_dir, f"etcd-v{etcd_version}-{plat}", "etcd")

    if os.path.exists(etcd_bin):
        print(f"Etcd {etcd_version} already exists")
        print("--- Done ---")
        return

    etcd_url = (
        "https://github.com/etcd-io/etcd/releases/"
        f"/download/v{etcd_version}/etcd-v{etcd_version}-{plat}.tar.gz"
    )
    if not os.path.exists(etcd_dir):
        print(f"Creating etcd directory {etcd_dir}...")
        os.mkdir(etcd_dir)
    else:
        print(f"Directory {etcd_dir} already exists")

    if not os.path.exists(etcd_arhive_name):
        print(f"Downloading {etcd_version} archive...")
        urlretrieve(etcd_url, etcd_arhive_name)
    else:
        print(f"Archive {etcd_arhive_name} already exists")

    with (tarfile.open(etcd_arhive_name, "r")) as tar_ref:
        print("Extracting the archive...")
        tar_ref.extractall(etcd_dir)

    print("--- Done ---")


def main():

    parser = argparse.ArgumentParser(
        description="Dependencies intaller",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--output",
        dest="installation_dir",
        default=os.path.join(HERE, "dependencies"),
        help=textwrap.dedent(
            """\
            The installation directory (absolute or relative path).
            If it doesn't exist, it will be created.
            If no directory is provided, it defaults to:
            --- %(default)s ---
            """
        ),
    )

    parser.add_argument(
        "--platform",
        dest="plat",
        default="linux-amd64",
        help=textwrap.dedent(
            """\
            The platform to download for.
            If no platform is provided, it defaults to:
            --- %(default)s ---
            """
        ),
    )

    parser.add_argument(
        "--traefik_version",
        dest="traefik_version",
        default="1.7.5",
        help=textwrap.dedent(
            """\
            The version of traefik to download.
            If no version is provided, it defaults to:
            --- %(default)s ---
            """
        ),
    )

    parser.add_argument(
        "--etcd_version",
        dest="etcd_version",
        default="3.3.10",
        help=textwrap.dedent(
            """\
            The version of etcd to download.
            If no version is provided, it defaults to:
            --- %(default)s ---
            """
        ),
    )

    args = parser.parse_args()
    deps_dir = args.installation_dir
    plat = args.plat
    traefik_version = args.traefik_version
    etcd_version = args.etcd_version

    if os.path.exists(deps_dir):
        print(f"Dependencies directory already exists.")
    else:
        print(f"Creating output directory {deps_dir}...")
        os.mkdir(deps_dir)

    install_traefik(deps_dir, plat, traefik_version)
    install_etcd(deps_dir, plat, etcd_version)


if __name__ == "__main__":
    main()
