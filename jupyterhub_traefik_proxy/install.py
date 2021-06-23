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

checksums_etcd = {
    "https://github.com/etcd-io/etcd/releases/download/v3.4.15/etcd-v3.4.15-linux-arm64.tar.gz": "fcc522275300cf90d42377106d47a2e384d1d2083af205cbb7833a79ef5a49d1",
    "https://github.com/etcd-io/etcd/releases/download/v3.4.15/etcd-v3.4.15-linux-amd64.tar.gz": "3bd00836ea328db89ecba3ed2155293934c0d09e64b53d6c9dfc0a256e724b81",
    "https://github.com/etcd-io/etcd/releases/download/v3.4.15/etcd-v3.4.15-darwin-amd64.tar.gz": "c596709069193bffc639a22558bdea4d801128e635909ea01a6fd5b5c85da729",
    "https://github.com/etcd-io/etcd/releases/download/v3.3.10/etcd-v3.3.10-linux-amd64.tar.gz": "1620a59150ec0a0124a65540e23891243feb2d9a628092fb1edcc23974724a45",
    "https://github.com/etcd-io/etcd/releases/download/v3.3.10/etcd-v3.3.10-darwin-amd64.tar.gz": "fac4091c7ba6f032830fad7809a115909d0f0cae5cbf5b34044540def743577b",
    "https://github.com/etcd-io/etcd/releases/download/v3.2.26/etcd-v3.2.26-linux-amd64.tar.gz": "127d4f2097c09d929beb9d3784590cc11102f4b4d4d4da7ad82d5c9e856afd38",
    "https://github.com/etcd-io/etcd/releases/download/v3.2.26/etcd-v3.2.26-darwin-amd64.zip": "0393e650ffa3e61b1fd07c61f8c78af1556896c300c9814545ff0e91f52c3513",
}

checksums_consul = {
    "https://releases.hashicorp.com/consul/1.9.4/consul_1.9.4_linux_amd64.zip": "da3919197ef33c4205bb7df3cc5992ccaae01d46753a72fe029778d7f52fb610",
    "https://releases.hashicorp.com/consul/1.9.4/consul_1.9.4_linux_arm64.zip": "012c552aff502f907416c9a119d2dfed88b92e981f9b160eb4fe292676afdaeb",
    "https://releases.hashicorp.com/consul/1.9.4/consul_1.9.4_darwin.zip": "c168240d52f67c71b30ef51b3594673cad77d0dbbf38c412b2ee30b39ef30843",
    "https://releases.hashicorp.com/consul/1.6.1/consul_1.6.1_linux_amd64.zip": "a8568ca7b6797030b2c32615b4786d4cc75ce7aee2ed9025996fe92b07b31f7e",
    "https://releases.hashicorp.com/consul/1.6.1/consul_1.6.1_darwin_amd64.zip": "4bc205e06b2921f998cb6ddbe70de57f8e558e226e44aba3f337f2f245678b85",
    "https://releases.hashicorp.com/consul/1.5.0/consul_1.5.0_linux_amd64.zip": "1399064050019db05d3378f757e058ec4426a917dd2d240336b51532065880b6",
    "https://releases.hashicorp.com/consul/1.5.0/consul_1.5.0_darwin_amd64.zip": "b4033ea6871fe6136ee5d940c834be2248463c3ec248dc22370e6d5360931325",
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
        "https://github.com/traefik/traefik/releases"
        f"/download/v{traefik_version}/{traefik_archive}"
    )

    if os.path.exists(traefik_bin) and os.path.exists(traefik_archive_path):
        print(f"Traefik already exists")
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
            raise IOError("Checksum failed")
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
                f"Etcd {etcd_version} not supported ! Or, at least, we don't "
                f"recognise {etcd_url} in our checksums", stacklevel=2,
            )
            os.chmod(etcd_bin, 0o755)
            os.chmod(etcdctl_bin, 0o755)
            print("--- Done ---")
            return
        else:
            checksum_etcd_archive = checksum_file(etcd_downloaded_archive)
            if checksum_etcd_archive == checksums_etcd[etcd_url]:
                os.chmod(etcd_bin, 0o755)
                os.chmod(etcdctl_bin, 0o755)
                print("--- Done ---")
                return
            else:
                print(f"checksum mismatch on {etcd_downloaded_archive}")
                os.remove(etcd_bin)
                os.remove(etcdctl_bin)
                os.remove(etcd_downloaded_archive)

    if not os.path.exists(etcd_downloaded_archive):
        print(f"Downloading {etcd_downloaded_dir_name} archive...")
        urlretrieve(etcd_url, etcd_downloaded_archive)
    else:
        print(f"Archive {etcd_downloaded_dir_name} already exists")

    if etcd_url in checksums_etcd:
        checksum_etcd_archive = checksum_file(etcd_downloaded_archive)
        if checksum_etcd_archive != checksums_etcd[etcd_url]:
            raise IOError("Checksum failed")
    else:
        warnings.warn(
            f"Etcd {etcd_version} not supported ! Or, at least, we don't "
            f"recognise {etcd_url} in our checksums",
            stacklevel=2
        )

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
                f"Consul {consul_version} not supported ! Or, at least we don't have "
                f"it {consul_url} in our checksums",
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
            f"Consul {consul_version} not supported ! Or, at least we don't have "
            f"it {consul_url} in our checksums",
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
                - v2.4.8-linux-amd64
                - v2.4.8-darwin-amd64
                - v2.4.8-windows-amd64
                - v2.3.7-linux-amd64
                - v2.3.7-darwin-amd64
                - v2.3.7-windows-amd64
                - v2.2.11-linux-amd64
                - v2.2.11-darwin-amd64
                - v2.2.11-windows-amd64
            - etcd:
                - v3.4.15-linux-amd64
                - v3.4.15-darwin-amd64
                - v3.4.15-windows-amd64
                - v3.3.10-linux-amd64
                - v3.3.10-darwin-amd64
                - v3.2.26-linux-amd64
                - v3.2.26-darwin-amd64
            - consul:
                - v1.9.4_darwin
                - v1.9.4_linux_amd64
                - v1.9.4_linux_arm64
                - v1.6.1_linux_amd64
                - v1.6.1_darwin_amd64
                - v1.5.0_linux_amd64
                - v1.5.0_darwin_amd64
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
        default="2.4.8",
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
        default="3.4.15",
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
        default="1.9.4",
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
