# How to make a release

`traefik-proxy` is a package [available on
PyPI](https://pypi.org/project/jupyterhub-traefik-proxy/).
The PyPI release is done automatically by TravisCI when a tag
is pushed.

For you to follow along according to these instructions, you need
to have push rights to the [traefik-proxy GitHub
repository](https://github.com/jupyterhub/traefik-proxy).

## Steps to make a release

1. Checkout master and make sure it is up to date.

   ```shell
   ORIGIN=${ORIGIN:-origin} # set to the canonical remote, e.g. 'upstream' if 'origin' is not the official repo
   git checkout master
   git fetch $ORIGIN master
   git reset --hard $ORIGIN/master
   # WARNING! This next command deletes any untracked files in the repo
   git clean -xfd
   ```

1. Update [changelog.rst](docs/source/changelog.rst) and add it to
   the working tree.
   
   ```shell
   git add traefik-proxy/docs/source/changelog.rst
   ```

   Tip: Identifying the changes can be made easier with the help of the
   [choldgraf/github-activity](https://github.com/choldgraf/github-activity)
   utility.

1. Set a shell variable to be the new version you want to release.
   The actual project version will be set from git automatically by versioneer.
   
   ```shell
   VERSION=...  # e.g. 1.2.3
   git commit -m "release $VERSION"
   ```

   Tip: You can get the current project version by checking the [latest
   tag on GitHub](https://github.com/jupyterhub/traefik-proxy/tags).
   
1. Push your commit to master.

   ```shell
   # first push commits without a tags to ensure the
   # commits comes through, because a tag can otherwise
   # be pushed all alone without company of rejected
   # commits, and we want have our tagged release coupled
   # with a specific commit in master
   git push $ORIGIN master
   ```

1. Create a git tag for the pushed release commit and push it.

   ```shell
   git tag -a $VERSION -m "release $VERSION"

   # then verify you tagged the right commit
   git log

   # then push it
   git push --follow-tags
   ```

