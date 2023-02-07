# How to make a release

`traefik-proxy` is a package [available on
PyPI](https://pypi.org/project/jupyterhub-traefik-proxy/). These are
instructions on how to make a release on PyPI.

For you to follow along according to these instructions, you need:

- To have push rights to the [jupyterhub-traefik-proxy GitHub
  repository](https://github.com/jupyterhub/traefik-proxy).

## Steps to make a release

1. Checkout main and make sure it is up to date.

   ```shell
   ORIGIN=${ORIGIN:-origin} # set to the canonical remote, e.g. 'upstream' if 'origin' is not the official repo
   git checkout main
   git fetch $ORIGIN main
   # WARNING! These next commands discard any changes or uncommitted files!
   git reset --hard $ORIGIN/main
   git clean -xfd
   ```

1. Update [changelog.md](docs/source/changelog.md) and add it to
   the working tree.

   ```shell
   git add traefik-proxy/docs/source/changelog.md
   ```

   Tip: Identifying the changes can be made easier with the help of the
   [choldgraf/github-activity](https://github.com/choldgraf/github-activity)
   utility.

1. Set a shell variable to be the new version you want to release.
   The actual project version will be detected automatically by versioneer
   from git tags inspection. The versioneer script will be run by setup.py
   when packaging is occurring.

   ```shell
   VERSION=...  # e.g. 1.2.3
   git commit -m "release $VERSION"
   ```

   Tip: You can get the current project version by checking the [latest
   tag on GitHub](https://github.com/jupyterhub/traefik-proxy/tags).

1. Create a git tag for the release commit and push them both.

   ```shell
   git tag -a $VERSION -m "release $VERSION"

   # then verify you tagged the right commit
   git log

   # then push it
   git push $ORIGIN --atomic --follow-tags
   ```
