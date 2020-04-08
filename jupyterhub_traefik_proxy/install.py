import sys
import os
from urllib.request import urlretrieve
import tarfile
import zipfile
import shutil
import argparse
import textwrap
import hashlib
import warnings

checksums_traefik = {
    "https://github.com/containous/traefik/releases/download/v2.2.0/traefik_v2.2.0_linux_amd64.tar.gz":
        "eddea0507ad715c723662e7c10fdab554eb64379748278cd2d09403063e3e32f",
    "https://github.com/containous/traefik/releases/download/v2.2.0/traefik_v2.2.0_darwin_amd64.tar.gz":
        "8bfa2393b265ef01aca12be94d67080961299968bd602f3708480eed273b95e0",
    "https://github.com/containous/traefik/releases/download/v2.2.0/traefik_v2.2.0_windows_amd64.zip":
        "9a794e395b7eba8d44118c4a1fb358fbf14abff3f5f5d264f46b1d6c243b9a5e",
}

checksums_etcd = {
    "https://github.com/etcd-io/etcd/releases/download/v3.4.7/etcd-v3.4.7-linux-amd64.tar.gz":
        "4ad86e663b63feb4855e1f3a647e719d6d79cf6306410c52b7f280fa56f8eb6b",
    "https://github.com/etcd-io/etcd/releases/download/v3.4.7/etcd-v3.4.7-darwin-amd64.zip":
        "ffe3237fcb70b7ce91c16518c2f62f3fa9ff74ddc10f7b6ca83a3b5b29ade19a",
    "https://github.com/etcd-io/etcd/releases/download/v3.4.7/etcd-v3.4.7-windows-amd64.zip":
        "3863ea59bcb407113524b51406810e33d58daff11ca10d1192f289185ae94ffe",
}

checksums_consul = {
    "https://releases.hashicorp.com/consul/1.7.2/consul_1.7.2_linux_amd64.zip":
        "5ab689cad175c08a226a5c41d16392bc7dd30ceaaf90788411542a756773e698",
    "https://releases.hashicorp.com/consul/1.7.2/consul_1.7.2_darwin_amd64.zip":
        "c474f00b022cae38acae2d19b2a707a4fcb08dfdd22875efeefdf052ce19c90b",
    "https://releases.hashicorp.com/consul/1.7.2/consul_1.7.2_windows_amd64.zip":
        "e9b9355f77f80b2c0940888cb0d27c44a5879c31e379ef21ffcfd36c91d202c1",
}


def checksum_file(path):
    """Compute the sha256 checksum of a path"""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def install_traefik(prefix, plat, traefik_version):
    plat = plat.replace("-", "_")
    if "windows" in plat:
        traefik_archive_extension = "zip"
        traefik_bin = os.path.join(prefix, "traefik.exe")
    else:
        traefik_archive_extension = "tar.gz"
        traefik_bin = os.path.join(prefix, "traefik")

    traefik_archive = "traefik_v" + traefik_version + "_" + plat + "." + traefik_archive_extension
    traefik_archive_path = os.path.join(prefix, traefik_archive)

    traefik_archive = "traefik_v" + traefik_version + "_" + plat + "." + traefik_archive_extension
    traefik_archive_path = os.path.join(prefix, traefik_archive)

    traefik_archive = "traefik_v" + traefik_version + "_" + plat + "." + traefik_archive_extension
    traefik_archive_path = os.path.join(prefix, traefik_archive)

    traefik_url = (
        "https://github.com/containous/traefik/releases"
        f"/download/v{traefik_version}/{traefik_archive}"
    )

    if os.path.exists(traefik_bin) and os.path.exists(traefik_archive_path):
        print(f"Traefik already exists")
        if traefik_url not in checksums_traefik:
            warnings.warn(
                f"Traefik {traefik_version} not supported !",
                stacklevel=2,
            )
            os.chmod(traefik_bin, 0o755)
            print("--- Done ---")
            return
        else:
            if checksum_file(traefik_archive_path) == checksums_traefik[traefik_url]:
                os.chmod(traefik_bin, 0o755)
                print("--- Done ---")
                return
            else:
                print(f"checksum mismatch on {traefik_archive_path}")
                os.remove(traefik_archive_path)
                os.remove(traefik_bin)

    if traefik_url in checksums_traefik:
        print(f"Downloading traefik {traefik_version}...")
        urlretrieve(traefik_url, traefik_archive_path)

        if checksum_file(traefik_archive_path) != checksums_traefik[traefik_url]:
            raise IOError("Checksum failed")

        print("Extracting the archive...")
        if traefik_archive_extension == "tar.gz":
            with tarfile.open(traefik_archive_path, "r") as tar_ref:
                tar_ref.extract("traefik", prefix)
        else:
            with zipfile.ZipFile(traefik_archive_path, "r") as zip_ref:
                zip_ref.extract("traefik.exe", prefix)

        os.chmod(traefik_bin, 0o755)
    else:
        warnings.warn(
            f"Traefik {traefik_version} not supported !",
            stacklevel=2,
        )

    print("--- Done ---")


def install_etcd(prefix, plat, etcd_version):
    etcd_downloaded_dir_name = f"etcd-v{etcd_version}-{plat}"
    if "linux" in plat:
        etcd_archive_extension = "tar.gz"
    else:
        etcd_archive_extension = "zip"
    etcd_downloaded_archive = os.path.join(
        prefix, etcd_downloaded_dir_name + "." + etcd_archive_extension
    )
    etcd_binaries = os.path.join(prefix, "etcd_binaries")

    etcd_bin = os.path.join(prefix, "etcd")
    etcdctl_bin = os.path.join(prefix, "etcdctl")

    etcd_url = (
        "https://github.com/etcd-io/etcd/releases"
        f"/download/v{etcd_version}/etcd-v{etcd_version}-{plat}.{etcd_archive_extension}"
    )

    if os.path.exists(etcd_bin) and os.path.exists(etcdctl_bin):
        print(f"Etcd and etcdctl already exist")
        if etcd_url not in checksums_etcd:
            warnings.warn(
                f"Etcd {etcd_version} not supported !",
                stacklevel=2,
            )
            os.chmod(etcd_bin, 0o755)
            os.chmod(etcdctl_bin, 0o755)
            print("--- Done ---")
            return
        else:
            if checksum_file(etcd_downloaded_archive) == checksums_etcd[etcd_url]:
                os.chmod(etcd_bin, 0o755)
                os.chmod(etcdctl_bin, 0o755)
                print("--- Done ---")
                return
            else:
                print(f"checksum mismatch on {etcd_downloaded_archive}")
                os.remove(etcd_bin)
                os.remove(etcdctl_bin)
                os.remove(etcd_downloaded_archive)

    if etcd_url in checksums_etcd:
        if not os.path.exists(etcd_downloaded_archive):
            print(f"Downloading {etcd_downloaded_dir_name} archive...")
            urlretrieve(etcd_url, etcd_downloaded_archive)
        else:
            print(f"Archive {etcd_downloaded_dir_name} already exists")

        if checksum_file(etcd_downloaded_archive) != checksums_etcd[etcd_url]:
            raise IOError("Checksum failed")

        print("Extracting the archive...")

        if etcd_archive_extension == "zip":
            with zipfile.ZipFile(etcd_downloaded_archive, "r") as zip_ref:
                zip_ref.extract(etcd_downloaded_dir_name + "/etcd", etcd_binaries)
                zip_ref.extract(etcd_downloaded_dir_name + "/etcdctl", etcd_binaries)
        else:
            with (tarfile.open(etcd_downloaded_archive, "r")) as tar_ref:
                tar_ref.extract(etcd_downloaded_dir_name + "/etcd", etcd_binaries)
                tar_ref.extract(etcd_downloaded_dir_name + "/etcdctl", etcd_binaries)

        shutil.copy(os.path.join(etcd_binaries, etcd_downloaded_dir_name, "etcd"), etcd_bin)
        shutil.copy(
            os.path.join(etcd_binaries, etcd_downloaded_dir_name, "etcdctl"), etcdctl_bin)

        os.chmod(etcd_bin, 0o755)
        os.chmod(etcdctl_bin, 0o755)

        # Cleanup
        shutil.rmtree(etcd_binaries)
    else:
        warnings.warn(
            f"Etcd {etcd_version} not supported !",
            stacklevel=2
        )

    print("--- Done ---")


def install_consul(prefix, plat, consul_version):
    plat = plat.replace("-", "_")
    consul_downloaded_dir_name = f"consul_v{consul_version}_{plat}"
    consul_archive_extension = "zip"

    consul_downloaded_archive = os.path.join(
        prefix, consul_downloaded_dir_name + "." + consul_archive_extension
    )
    consul_binaries = os.path.join(prefix, "consul_binaries")
    consul_bin = os.path.join(prefix, "consul")

    consul_url = (
        "https://releases.hashicorp.com/consul/"
        f"{consul_version}/consul_{consul_version}_{plat}.{consul_archive_extension}"
    )

    if os.path.exists(consul_bin):
        print(f"Consul already exists")
        if consul_url not in checksums_consul:
            warnings.warn(
                f"Consul {consul_version} not supported !",
                stacklevel=2,
            )
            os.chmod(consul_bin, 0o755)
            print("--- Done ---")
            return
        else:
            if checksum_file(consul_downloaded_archive) == checksums_consul[consul_url]:
                os.chmod(consul_bin, 0o755)
                print("--- Done ---")
                return
            else:
                print(f"checksum mismatch on {consul_downloaded_archive}")
                os.remove(consul_bin)
                os.remove(consul_downloaded_archive)

    if consul_url in checksums_consul:
        if not os.path.exists(consul_downloaded_archive):
            print(f"Downloading {consul_downloaded_dir_name} archive...")
            urlretrieve(consul_url, consul_downloaded_archive)
        else:
            print(f"Archive {consul_downloaded_dir_name} already exists")

        if checksum_file(consul_downloaded_archive) != checksums_consul[consul_url]:
            raise IOError("Checksum failed")

        with zipfile.ZipFile(consul_downloaded_archive, "r") as zip_ref:
            zip_ref.extract("consul", consul_binaries)

        shutil.copy(os.path.join(consul_binaries, "consul"), consul_bin)
        os.chmod(consul_bin, 0o755)
        # Cleanup
        shutil.rmtree(consul_binaries)
    else:
        warnings.warn(
            f"Consul {consul_version} not supported !",
            stacklevel=2,
        )

    print("--- Done ---")


def main():

    parser = argparse.ArgumentParser(
        description="Dependencies intaller",
        epilog=textwrap.dedent(
            """\
            Checksums available for:
            - traefik:
                - v2.2.0-linux-amd64
                - v2.2.0-darwin-amd64
                - v2.2.0-windows-amd64
            - etcd:
                - v3.4.7-linux-amd64
                - v3.4.7-darwin-amd64
                - v3.4.7-windows-amd64
            - consul:
                - v1.7.2_linux_amd64
                - v1.7.2_darwin_amd64
                - v1.7.2_windows_amd64
            """
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--output",
        dest="installation_dir",
        default="./dependencies",
        help=textwrap.dedent(
            """\
            The installation directory (absolute or relative path).
            If it doesn't exist, it will be created.
            If no directory is provided, it defaults to:
            --- %(default)s ---
            """
        ),
    )

    default_platform = sys.platform + "-amd64"

    parser.add_argument(
        "--platform",
        dest="plat",
        default=default_platform,
        help=textwrap.dedent(
            """\
            The platform to download for.
            If no platform is provided, it defaults to:
            --- %(default)s ---
            """
        ),
    )

    parser.add_argument(
        "--traefik",
        action="store_true",
        help=textwrap.dedent(
            """\
            Whether or not to install traefik.
            By default traefik is NOT going to be installed.
            """
        ),
    )

    parser.add_argument(
        "--traefik-version",
        dest="traefik_version",
        default="2.2.0",
        help=textwrap.dedent(
            """\
            The version of traefik to download.
            If no version is provided, it defaults to:
            --- %(default)s ---
            """
        ),
    )

    parser.add_argument(
        "--etcd",
        action="store_true",
        help=textwrap.dedent(
            """\
            Whether or not to install etcd.
            By default etcd is NOT going to be installed.
            """
        ),
    )

    parser.add_argument(
        "--etcd-version",
        dest="etcd_version",
        default="3.4.7",
        help=textwrap.dedent(
            """\
            The version of etcd to download.
            If no version is provided, it defaults to:
            --- %(default)s ---
            """
        ),
    )

    parser.add_argument(
        "--consul",
        action="store_true",
        help=textwrap.dedent(
            """\
            Whether or not to install consul.
            By default consul is NOT going to be installed:
            """
        ),
    )

    parser.add_argument(
        "--consul-version",
        dest="consul_version",
        default="1.7.2",
        help=textwrap.dedent(
            """\
            The version of consul to download.
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
    consul_version = args.consul_version

    if not args.traefik and not args.etcd and not args.consul:
        print(
            """Please specify what binary to install.
            Tip: python3 -m jupyterhub_traefik_proxy.install --help
            to get the list of available options."""
        )
        return

    if os.path.exists(deps_dir):
        print(f"Using existing output directory {deps_dir}...")
    else:
        print(f"Creating output directory {deps_dir}...")
        os.makedirs(deps_dir)

    if args.traefik:
        install_traefik(deps_dir, plat, traefik_version)
    if args.etcd:
        install_etcd(deps_dir, plat, etcd_version)
    if args.consul:
        install_consul(deps_dir, plat, consul_version)


if __name__ == "__main__":
    main()
