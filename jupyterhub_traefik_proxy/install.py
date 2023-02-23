import argparse
import hashlib
import os
import platform
import sys
import tarfile
import textwrap
import warnings
import zipfile
from urllib.request import urlretrieve

checksums_traefik = {
    "https://github.com/traefik/traefik/releases/download/v2.4.8/traefik_v2.4.8_linux_arm64.tar.gz": "0931fdd9c855fcafd38eba7568a1d287200fad5afd1aef7d112fb3a48d822fcc",
    "https://github.com/traefik/traefik/releases/download/v2.4.8/traefik_v2.4.8_linux_amd64.tar.gz": "de8d56f6777c5098834d4f8d9ed419b7353a3afe913393a55b6fd14779564129",
    "https://github.com/traefik/traefik/releases/download/v2.4.8/traefik_v2.4.8_darwin_amd64.tar.gz": "7d946baa422acfcf166e19779052c005722db03de3ab4d7aff586c4b4873a0f3",
    "https://github.com/traefik/traefik/releases/download/v2.4.8/traefik_v2.4.8_windows_amd64.zip": "4203443cb1e91d76f81d1e2a41fb70e66452d951b1ffd8964218a7bc211c377d",
    "https://github.com/traefik/traefik/releases/download/v2.3.7/traefik_v2.3.7_linux_amd64.tar.gz": "a357d40bc9b81ae76070a2bc0334dfd15e77143f41415a93f83bb53af1756909",
    "https://github.com/traefik/traefik/releases/download/v2.3.7/traefik_v2.3.7_darwin_amd64.tar.gz": "c84fc21b8ee34bba8a66f0f9e71c6c2ea69684ac6330916551f1f111826b9bb3",
    "https://github.com/traefik/traefik/releases/download/v2.3.7/traefik_v2.3.7_windows_amd64.zip": "eb54b1c9c752a6eaf48d28ff8409c17379a29b9d58390107411762ab6e4edfb4",
    "https://github.com/traefik/traefik/releases/download/v2.2.11/traefik_v2.2.11_linux_amd64.tar.gz": "b677386423403c63fb9ac9667d39591be587a1a4928afc2e59449c78343bad9c",
    "https://github.com/traefik/traefik/releases/download/v2.2.11/traefik_v2.2.11_darwin_amd64.tar.gz": "efb1c2bc23e16a9083e5a210594186d026cdec0b522a6b4754ceff43b07d8031",
    "https://github.com/traefik/traefik/releases/download/v2.2.11/traefik_v2.2.11_windows_amd64.zip": "ee867133e00b2d8395c239d8fed04a26b362e650b371dc0b653f0ee9d52471e6",
}

machine_map = {
    "x86_64": "amd64",
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

    traefik_archive = (
        "traefik_v" + traefik_version + "_" + plat + "." + traefik_archive_extension
    )
    traefik_archive_path = os.path.join(prefix, traefik_archive)

    traefik_url = (
        "https://github.com/traefik/traefik/releases"
        f"/download/v{traefik_version}/{traefik_archive}"
    )

    if os.path.exists(traefik_bin) and os.path.exists(traefik_archive_path):
        print("Traefik already exists")
        if traefik_url not in checksums_traefik:
            warnings.warn(
                f"Traefik {traefik_version} not tested !",
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

    print(f"Downloading traefik {traefik_version} from {traefik_url}...")
    urlretrieve(traefik_url, traefik_archive_path)

    if traefik_url in checksums_traefik:
        if checksum_file(traefik_archive_path) != checksums_traefik[traefik_url]:
            raise OSError("Checksum failed")
    else:
        warnings.warn(
            f"Traefik {traefik_version} not tested !",
            stacklevel=2,
        )

    print("Extracting the archive...")
    if traefik_archive_extension == "tar.gz":
        with tarfile.open(traefik_archive_path, "r") as tar_ref:
            tar_ref.extract("traefik", prefix)
    else:
        with zipfile.ZipFile(traefik_archive_path, "r") as zip_ref:
            zip_ref.extract("traefik.exe", prefix)

    os.chmod(traefik_bin, 0o755)
    os.unlink(traefik_archive_path)
    print("--- Done ---")


def main():
    parser = argparse.ArgumentParser(
        description="Dependencies intaller",
        epilog=textwrap.dedent(
            """\
            Checksums available for:
            - traefik:
                - v2.4.8-linux-amd64
                - v2.4.8-darwin-amd64
                - v2.4.8-windows-amd64
                - v2.3.7-linux-amd64
                - v2.3.7-darwin-amd64
                - v2.3.7-windows-amd64
                - v2.2.11-linux-amd64
                - v2.2.11-darwin-amd64
                - v2.2.11-windows-amd64
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

    machine = platform.machine()
    machine = machine_map.get(machine, machine)
    default_platform = f"{sys.platform}-{machine}"

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
        help="DEPRECATED, IGNORED",
    )

    parser.add_argument(
        "--traefik-version",
        dest="traefik_version",
        default="2.4.8",
        help=textwrap.dedent(
            """\
            The version of traefik to download.
            If no version is provided, it defaults to:
            --- %(default)s ---
            """
        ),
    )
    if "--etcd" in sys.argv:
        sys.exit(
            "Installing etcd is no longer supported. Visit https://github.com/etcd-io/etcd/releases/"
        )
    if "--consul" in sys.argv:
        sys.exit(
            "Installing consul is no longer supported. Visit https://developer.hashicorp.com/consul/downloads"
        )

    args = parser.parse_args()
    deps_dir = args.installation_dir
    plat = args.plat
    traefik_version = args.traefik_version

    if args.traefik:
        print(
            "Specifying --traefik is deprecated and ignored. Only installing traefik is supported.",
            file=sys.stderr,
        )

    if os.path.exists(deps_dir):
        print(f"Using existing output directory {deps_dir}...")
    else:
        print(f"Creating output directory {deps_dir}...")
        os.makedirs(deps_dir)

    install_traefik(deps_dir, plat, traefik_version)


if __name__ == "__main__":
    main()
