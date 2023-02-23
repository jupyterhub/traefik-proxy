"""Install jupyterhub-traefik-proxy

Usage:

    pip install [-e] .
"""

import os
import sys

from setuptools import find_packages, setup
from setuptools.command.bdist_egg import bdist_egg

# ensure cwd is on sys.path
# workaround bug in pip 19.0
here = os.path.dirname(__file__)
if here not in sys.path:
    sys.path.insert(0, here)

import versioneer

cmdclass = versioneer.get_cmdclass()


class bdist_egg_disabled(bdist_egg):
    """Disabled version of bdist_egg

    Prevents setup.py install from performing setuptools' default easy_install,
    which it should never ever do.
    """

    def run(self):
        sys.exit(
            "Aborting implicit building of eggs. Use `pip install .` to install from source."
        )


if "bdist_egg" not in sys.argv:
    cmdclass["bdist_egg"] = bdist_egg_disabled

with open("README.md", encoding="utf8") as f:
    readme = f.read()

setup(
    name="jupyterhub-traefik-proxy",
    version=versioneer.get_version(),
    install_requires=open("requirements.txt").read().splitlines(),
    python_requires=">=3.6",
    author="Project Jupyter Contributors",
    author_email="jupyter@googlegroups.com",
    url="https://jupyterhub-traefik-proxy.readthedocs.io",
    project_urls={
        "Documentation": "https://jupyterhub-traefik-proxy.readthedocs.io",
        "Source": "https://github.com/jupyterhub/traefik-proxy/",
        "Tracker": "https://github.com/jupyter/traefik-proxy/issues",
    },
    # this should be a whitespace separated string of keywords, not a list
    keywords="jupyter jupyterhub traefik proxy",
    description="JupyterHub proxy implementation with traefik",
    long_description=readme,
    long_description_content_type="text/markdown",
    license="BSD",
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
    packages=find_packages(),
    include_package_data=True,
    cmdclass=cmdclass,
    entry_points={
        "jupyterhub.proxies": [
            "traefik_consul = jupyterhub_traefik_proxy.consul:TraefikConsulProxy",
            "traefik_etcd = jupyterhub_traefik_proxy.etcd:TraefikEtcdProxy",
            "traefik_file = jupyterhub_traefik_proxy.fileprovider:TraefikFileProviderProxy",
            "traefik_toml = jupyterhub_traefik_proxy.toml:TraefikTomlProxy",
        ]
    },
)
