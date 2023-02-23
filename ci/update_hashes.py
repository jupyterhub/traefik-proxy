#!/usr/bin/env python3
"""Update traefik hashes in install.py

Provides two commands:

- `add` fetches a traefik release and adds the checksums to install.py.
  If no version is specified, the latest stable release will be added.
- `latest` lists the latest releases
"""

import re
import warnings
from pathlib import Path

import click
import requests
from github import Github as GitHub
from packaging.version import parse as parse_version

gh = GitHub()

repo_path = Path(__file__).parent.resolve().parent
checksums_txt = repo_path / "jupyterhub_traefik_proxy" / "checksums.txt"


def write_checksums(checksums_text_to_add):
    """Add the body of a new checksums.txt to our merged checksums.txt

    Merges lines, sorts by version, and removes duplicates
    """

    with checksums_txt.open() as f:
        before_checksums = {line.strip() for line in f.readlines()}

    after_checksums = set()
    after_checksums.update(before_checksums)
    after_checksums.update(checksums_text_to_add.splitlines())

    if after_checksums == before_checksums:
        print("No new checksums to add")
        return

    def _sort_key(line):
        """Sort filenames by version"""
        if not line.strip():
            return (parse_version("0.0"), "")
        print(line)
        checksum, filename = line.split()
        vs = re.search(r'v\d+\.\d+\.\d+', filename).group(0)
        return (parse_version(vs), filename)

    checksum_lines = sorted(after_checksums, key=_sort_key, reverse=True)
    with checksums_txt.open("w") as f:
        for line in checksum_lines:
            f.write(line + "\n")

    print(f"Wrote {len(checksum_lines)} checksums to {checksums_txt}")


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

    # download checksum file in standard format
    r = requests.get(checksum_asset.browser_download_url)
    r.raise_for_status()
    return r.text


# click command group
@click.group(help=__doc__)
def cli():
    pass


@cli.command()
@click.argument(
    "version",
    default="",
    type=str,
)
def add(version):
    """Add one traefik release to hashes in install.py

    This downloads and parses the checksum file stored in each traefik release,
    and adds the resulting checksums to install.py.

    `version` should be the git tag for the release (starts with 'v').
    If unspecified, the latest stable release will be added.
    """

    repo = gh.get_repo("traefik/traefik")
    if version:
        if not version.startswith("v"):
            version = "v" + version
        release = repo.get_release(version)
    else:
        # get latest non-prerelease version by default
        release = get_latest_releases(repo, 1)[0]
    print(f"Fetching checksums for traefik {release.tag_name}")
    new_checksums = fetch_checksums(release)
    write_checksums(new_checksums)
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
