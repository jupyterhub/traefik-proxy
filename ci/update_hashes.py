#!/usr/bin/env python3
"""Update traefik hashes in install.py

Provides two commands:

- `add` fetches a traefik release and adds the checksums to install.py.
  If no version is specified, the latest stable release will be added.
- `latest` lists the latest releases
"""

import warnings
from pathlib import Path

import click
import requests
from github import Github as GitHub
from packaging.version import parse as parse_version

gh = GitHub()

repo_path = Path(__file__).parent.resolve().parent
install_py = repo_path / "jupyterhub_traefik_proxy" / "install.py"


def read_install_py():
    """Parse our install.py

    Returns:

    - before_py - text before checksums
    - after_py - text after checksums
    - checksums - parsed checksums dict
    """
    before_py = []
    checksums_py = []
    after_py = []
    with install_py.open() as f:
        line_iter = iter(f.readlines())
        # read before
        for line in line_iter:
            before_py.append(line)
            if 'BEGIN CHECKSUMS' in line:
                break

        for line in line_iter:
            if 'END CHECKSUMS' in line:
                break
            checksums_py.append(line)

        after_py.append(line)
        for line in line_iter:
            after_py.append(line)

    ns = {}
    exec("".join(checksums_py), {}, ns)
    return "".join(before_py), "".join(after_py), ns["checksums_traefik"]


def write_install_py(checksums):
    """Write the updated install.py, adding `checksums`

    If there are no new checksums, nothing is written.

    After running, autoformatting will need to be applied to install.py.
    """
    before_py, after_py, before_checksums = read_install_py()
    new_checksums = {}
    new_checksums.update(checksums)
    new_checksums.update(before_checksums)
    if new_checksums == before_checksums:
        print("No new checksums to add")
        return

    with install_py.open("w") as f:
        f.write(before_py)
        f.write(f"\nchecksums_traefik = {repr(new_checksums)}\n\n")
        f.write(after_py)
    print(f"Wrote {len(checksums)} checksums to {install_py}")


def fetch_checksums(release):
    """Fetch checksums for assets in a specific release

    Assumes standard checksum file name and format used by traefik releases.
    """

    # find the checksum file in the assets
    assets_by_name = {}
    checksum_asset = None
    for asset in release.get_assets():
        assets_by_name[asset.name] = asset
        if "checksums" in asset.name:
            checksum_asset = asset

    if checksum_asset is None:
        raise ValueError(f"checksum file not found in {list(assets_by_name.keys())}")

    # download and parse into a dict
    r = requests.get(checksum_asset.browser_download_url)
    r.raise_for_status()
    checksums = {}
    for line in r.text.strip().splitlines():
        checksum, name = line.split()
        # resolve name 'traefik.tar.gz' to full download URL
        url = assets_by_name[name].browser_download_url
        checksums[url] = checksum
    return checksums


# click command group
@click.group(help=__doc__)
def cli():
    pass


@cli.command()
@click.option(
    "--version",
    default=None,
    type=str,
    help="The tag for the traefik release to add (starts with 'v'). If not specified, will find and add the latest stable release.",
)
def add(version):
    """Add one traefik release to hashes in install.py

    This downloads and parses the checksum file stored in each traefik release,
    and adds the resulting checksums to install.py.
    """

    repo = gh.get_repo("traefik/traefik")
    if version:
        release = repo.get_release(version)
    else:
        # get latest non-prerelease version by default
        release = get_latest_releases(repo, 1)[0]
    print(f"Fetching checksums for traefik {release.tag_name}")
    new_checksums = fetch_checksums(release)
    write_install_py(new_checksums)
    print(
        "If you've added a new latest version of traefik, consider updating the default version in install.py as well."
    )


def get_latest_releases(repo, limit=10):
    """Get the latest LIMIT releases for a repo

    Descending order by version, excluding prereleases
    """
    releases = []
    for release in repo.get_releases():
        try:
            v = parse_version(release.tag_name)
        except ValueError:
            warnings.warn(f"Not a valid version: {release.tag_name}")
            continue

        if v.is_prerelease:
            # excluded prereleases
            continue

        releases.append(release)
        if len(releases) >= limit:
            break
    releases = sorted(
        releases, key=lambda release: parse_version(release.tag_name), reverse=True
    )
    return releases


@cli.command()
@click.option("-n", type=int, default=10, help="Number of releases to show")
def latest(n=10):
    """Display the latest N releases of traefik

    Provides possible inputs to `add`.

    You could also go to https://github.com/traefik/traefik/releases
    """
    for release in get_latest_releases(gh.get_repo("traefik/traefik"), n):
        print(f"{release.tag_name}: {release.created_at.date()}")


if __name__ == "__main__":
    cli()
