# How to make a release

`traefik-proxy` is a package [available on
PyPI](https://pypi.org/project/jupyterhub-traefik-proxy/). These are
instructions on how to make a release on PyPI.

For you to follow along according to these instructions, you need:

- To have push rights to the [jupyterhub-traefik-proxy GitHub
  repository](https://github.com/jupyterhub/traefik-proxy).

## Steps to make a release

1. Create a PR updating `docs/source/changelog.md` with [github-activity][] and
   continue only when its merged.

   ```shell
   pip install github-activity

   github-activity --heading-level=3 jupyterhub/jupyterhub
   ```

1. Checkout main and make sure it is up to date.

   ```shell
   git checkout main
   git fetch origin main
   git reset --hard origin/main
   ```

1. Update the version, make commits, and push a git tag with `tbump`.

   ```shell
   pip install tbump
   tbump --dry-run ${VERSION}

   tbump ${VERSION}
   ```

   Following this, the [CI system][] will build and publish a release.

1. Reset the version back to dev, e.g. `2.1.0.dev` after releasing `2.0.0`

   ```shell
   tbump --no-tag ${NEXT_VERSION}.dev
   ```

[ci system]: https://github.com/jupyterhub/traefik-proxy/actions
[github-activity]: https://github.com/executablebooks/github-activity
