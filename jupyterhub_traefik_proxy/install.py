import sys
import os
from urllib.request import urlretrieve
import tarfile
import zipfile
import shutil
import argparse
import textwrap
import hashlib

checksums_traefik = {
    "v1.7.5-linux-amd64": "4417a9d83753e1ad6bdd64bbbeaeb4b279bcc71542e779b7bcb3b027c6e3356e",
    "v1.7.5-darwin-amd64": "379d4af242743a3fe44b44a1ee6df68ea8332578d85de35f264e062c19fd20a0",
    "v1.7.0-linux-amd64": "b84cb03e8a175b8b7d1a30246d19705f607c6ae5ee89f2dca7a1adccab919135",
    "v1.7.0-darwin-amd64": "3000cb9f8ed567e9bc567cce33107f6877f2017c69fae8ac235b51a7a94229bf",
}

checksums_etcd = {
    "v3.3.10-linux-amd64": "9627d4fe4f402b52ec715aa50491539aded62dd7d426bdec764571818efd2ff8",
    "v3.3.10-darwin-amd64": "670e22467ba6c63b2af08cc156cd7b84d94c98319893d105fe7f33fbbbe3c68f",
    "v3.2.25-linux-amd64": "fd006bc79a49453bf42ea0a245535ad1917f125f740ba100b8300c012c581612",
    "v3.2.25-darwin-amd64": "f5ab88a91eeb27aae7600d00f41807cec373ad6da9c40a6c28acbc8b850f1c10",
}

checksums_etcdctl = {
    "v3.3.10-linux-amd64": "519e571cf605236bdd7f3b6e3f51505de72b16747863a573503a1b806d35d975",
    "v3.3.10-darwin-amd64": "5a7ea25b70974bb39597420a4e2a7ee3c14d0e793509b3a5ce5704eb1ada01f1",
    "v3.2.25-linux-amd64": "cdadcad2894078c1c07bf0b83d61bb4bb47f929951429750bb2a573190deb84e",
    "v3.2.25-darwin-amd64": "4996b2513c8c9f445fcf0604f12573e49ad09c73d022576792e4cd28daecfd41",
}


def checksum_file(path):
    """Compute the sha256 checksum of a path"""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def install_traefik(prefix, plat, traefik_version):
    traefik_bin = os.path.join(prefix, "traefik")

    if os.path.exists(traefik_bin):
        print(f"Traefik already exists")
        checksum = checksum_file(traefik_bin)
        if checksum == checksums_traefik[f"v{traefik_version}-{plat}"]:
            os.chmod(traefik_bin, 0o755)
            print("--- Done ---")
            return
        else:
            print(f"checksum mismatch on {traefik_bin}")
            os.remove(traefik_bin)

    traefik_url = (
        "https://github.com/containous/traefik/releases"
        f"/download/v{traefik_version}/traefik_{plat}"
    )

    print(f"Downloading traefik {traefik_version}...")
    urlretrieve(traefik_url, traefik_bin)

    checksum = checksum_file(traefik_bin)
    if checksum != checksums_traefik[f"v{traefik_version}-{plat}"]:
        raise IOError("Checksum failed")

    os.chmod(traefik_bin, 0o755)

    print("--- Done ---")


def install_etcd(prefix, plat, etcd_version):
    etcd_downloaded_dir_name = f"etcd-v{etcd_version}-{plat}"
    etcd_archive_extension = ".tar.gz"
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

    if os.path.exists(etcd_bin) and os.path.exists(etcdctl_bin):
        print(f"Etcd and etcdctl already exist")
        checksum_etcd = checksum_file(etcd_bin)
        checksum_etcdctl = checksum_file(etcdctl_bin)
        if (
            checksum_etcd == checksums_etcd[f"v{etcd_version}-{plat}"]
            and checksum_etcdctl == checksums_etcdctl[f"v{etcd_version}-{plat}"]
        ):
            os.chmod(etcd_bin, 0o755)
            os.chmod(etcdctl_bin, 0o755)
            print("--- Done ---")
            return
        else:
            print(f"checksum mismatch on etcd")
            os.remove(etcd_bin)
            os.remove(etcdctl_bin)

    etcd_url = (
        "https://github.com/etcd-io/etcd/releases/"
        f"/download/v{etcd_version}/etcd-v{etcd_version}-{plat}.{etcd_archive_extension}"
    )
    if not os.path.exists(etcd_downloaded_archive):
        print(f"Downloading {etcd_downloaded_dir_name} archive...")
        urlretrieve(etcd_url, etcd_downloaded_archive)
    else:
        print(f"Archive {etcd_downloaded_dir_name} already exists")

    if etcd_archive_extension == "zip":
        with zipfile.ZipFile(etcd_downloaded_archive, "r") as zip_ref:
            zip_ref.extract(etcd_downloaded_dir_name + "/etcd", etcd_binaries)
            zip_ref.extract(etcd_downloaded_dir_name + "/etcdctl", etcd_binaries)
    else:
        with (tarfile.open(etcd_downloaded_archive, "r")) as tar_ref:
            print("Extracting the archive...")
            tar_ref.extract(etcd_downloaded_dir_name + "/etcd", etcd_binaries)
            tar_ref.extract(etcd_downloaded_dir_name + "/etcdctl", etcd_binaries)

    shutil.copy(os.path.join(etcd_binaries, etcd_downloaded_dir_name, "etcd"), etcd_bin)
    shutil.copy(
        os.path.join(etcd_binaries, etcd_downloaded_dir_name, "etcdctl"), etcdctl_bin
    )

    checksum_etcd = checksum_file(etcd_bin)
    checksum_etcdctl = checksum_file(etcdctl_bin)
    if (
        checksum_etcd != checksums_etcd[f"v{etcd_version}-{plat}"]
        and checksum_etcdctl != checksums_etcdctl[f"v{etcd_version}-{plat}"]
    ):
        raise IOError("Checksum failed")

    os.chmod(etcd_bin, 0o755)
    os.chmod(etcdctl_bin, 0o755)

    # Cleanup
    shutil.rmtree(etcd_binaries)
    os.remove(etcd_downloaded_archive)

    print("--- Done ---")


def main():

    parser = argparse.ArgumentParser(
        description="Dependencies intaller",
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
        "--traefik-version",
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
        "--etcd-version",
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
        os.makedirs(deps_dir)

    install_traefik(deps_dir, plat, traefik_version)
    install_etcd(deps_dir, plat, etcd_version)


if __name__ == "__main__":
    main()
