# Changelog

For detailed changes from the prior release, click on the version number
and its link will bring up a GitHub listing of changes. Use `git log` on
the command line for details.

### [0.3.0](https://github.com/jupyterhub/traefik-proxy/compare/0.2.0...0.3.0) 2021-10-18

#### Enhancements made

- Support ARM in binary package installs [#129](https://github.com/jupyterhub/traefik-proxy/pull/129) ([@yuvipanda](https://github.com/yuvipanda))

#### Bugs fixed

- Fix handling default server routes in TraefikTomlProxy [#131](https://github.com/jupyterhub/traefik-proxy/pull/131) ([@dolfinus](https://github.com/dolfinus))
- Make etcd3 & python-consul2 soft dependencies [#127](https://github.com/jupyterhub/traefik-proxy/pull/127) ([@yuvipanda](https://github.com/yuvipanda))

#### Continuous integration

- ci: don't run tests if docs change [#139](https://github.com/jupyterhub/traefik-proxy/pull/139) ([@consideRatio](https://github.com/consideRatio))
- ci/docs: install autodocs-traits as a PyPI package & pin sphinx [#138](https://github.com/jupyterhub/traefik-proxy/pull/138) ([@consideRatio](https://github.com/consideRatio))

#### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/traefik-proxy/graphs/contributors?from=2021-02-24&to=2021-10-18&type=c))

[@alexleach](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Aalexleach+updated%3A2021-02-24..2021-10-18&type=Issues) | [@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3AconsideRatio+updated%3A2021-02-24..2021-10-18&type=Issues) | [@dolfinus](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Adolfinus+updated%3A2021-02-24..2021-10-18&type=Issues) | [@GeorgianaElena](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3AGeorgianaElena+updated%3A2021-02-24..2021-10-18&type=Issues) | [@yuvipanda](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Ayuvipanda+updated%3A2021-02-24..2021-10-18&type=Issues)

## [0.2.0](https://github.com/jupyterhub/traefik-proxy/compare/0.1.6...0.2.0) 2021-02-24

### Bugs fixed

- fix Escape character \_ cannot be a safe character #109 [#110](https://github.com/jupyterhub/traefik-proxy/pull/110) ([@mofanke](https://github.com/mofanke))

### Maintenance and upkeep improvements

- Switch to pydata-sphinx-theme and myst-parser [#122](https://github.com/jupyterhub/traefik-proxy/pull/122) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- Try unpinning deps and use a more up to date python consul client [#115](https://github.com/jupyterhub/traefik-proxy/pull/115) ([@GeorgianaElena](https://github.com/GeorgianaElena))

### Other merged PRs

- Remove CircleCI docs build since now we're using the RTD CI [#121](https://github.com/jupyterhub/traefik-proxy/pull/121) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- Do not freeze requirements [#120](https://github.com/jupyterhub/traefik-proxy/pull/120) ([@minrk](https://github.com/minrk))
- Update readthedocs config options and version [#119](https://github.com/jupyterhub/traefik-proxy/pull/119) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- pip-compile is actually just pip in dependabots config file [#117](https://github.com/jupyterhub/traefik-proxy/pull/117) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- Freeze requirements and setup dependabot [#116](https://github.com/jupyterhub/traefik-proxy/pull/116) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- ci: make pushing tags trigger release workflow properly [#114](https://github.com/jupyterhub/traefik-proxy/pull/114) ([@consideRatio](https://github.com/consideRatio))
- Travis -> GitHub workflows [#113](https://github.com/jupyterhub/traefik-proxy/pull/113) ([@GeorgianaElena](https://github.com/GeorgianaElena))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/traefik-proxy/graphs/contributors?from=2020-05-16&to=2021-02-24&type=c))

[@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3AconsideRatio+updated%3A2020-05-16..2021-02-24&type=Issues) | [@GeorgianaElena](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3AGeorgianaElena+updated%3A2020-05-16..2021-02-24&type=Issues) | [@manics](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Amanics+updated%3A2020-05-16..2021-02-24&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Aminrk+updated%3A2020-05-16..2021-02-24&type=Issues) | [@mofanke](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Amofanke+updated%3A2020-05-16..2021-02-24&type=Issues)

## [0.1.6](https://github.com/jupyterhub/traefik-proxy/compare/0.1.5...0.1.6) 2020-05-16

### Merged PRs

- Fix circular reference error [#107](https://github.com/jupyterhub/traefik-proxy/pull/107) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- fix TypeError: 'NoneType' object is not iterable, in delete_route when route doesn't exist [#104](https://github.com/jupyterhub/traefik-proxy/pull/104) ([@mofanke](https://github.com/mofanke))
- Update etcd.py [#102](https://github.com/jupyterhub/traefik-proxy/pull/102) ([@mofanke](https://github.com/mofanke))
- New Proxy config option traefik_api_validate_cert [#98](https://github.com/jupyterhub/traefik-proxy/pull/98) ([@devnull-mr](https://github.com/devnull-mr))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/traefik-proxy/graphs/contributors?from=2020-03-31&to=2020-05-16&type=c))

[@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3AconsideRatio+updated%3A2020-03-31..2020-05-16&type=Issues) | [@devnull-mr](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Adevnull-mr+updated%3A2020-03-31..2020-05-16&type=Issues) | [@GeorgianaElena](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3AGeorgianaElena+updated%3A2020-03-31..2020-05-16&type=Issues) | [@mofanke](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Amofanke+updated%3A2020-03-31..2020-05-16&type=Issues)

## [0.1.5](https://github.com/jupyterhub/traefik-proxy/compare/0.1.4...0.1.5) 2020-03-31

### Merged PRs

- Fix named servers routing [#96](https://github.com/jupyterhub/traefik-proxy/pull/96) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- Show a message when no binary is provided to the installer [#95](https://github.com/jupyterhub/traefik-proxy/pull/95) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- Update install utility docs [#93](https://github.com/jupyterhub/traefik-proxy/pull/93) ([@jtpio](https://github.com/jtpio))
- Travis deploy tags to PyPI [#89](https://github.com/jupyterhub/traefik-proxy/pull/89) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- Update README [#87](https://github.com/jupyterhub/traefik-proxy/pull/87) ([@consideRatio](https://github.com/consideRatio))
- Handle ssl [#84](https://github.com/jupyterhub/traefik-proxy/pull/84) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- CONTRIBUTING: use long option in "pip install -e" [#82](https://github.com/jupyterhub/traefik-proxy/pull/82) ([@muxator](https://github.com/muxator))
- Change traefik default version [#81](https://github.com/jupyterhub/traefik-proxy/pull/81) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- Add info about TraefikConsulProxy in readme [#80](https://github.com/jupyterhub/traefik-proxy/pull/80) ([@GeorgianaElena](https://github.com/GeorgianaElena))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/traefik-proxy/graphs/contributors?from=2019-09-20&to=2020-03-31&type=c))

[@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3AconsideRatio+updated%3A2019-09-20..2020-03-31&type=Issues) | [@devnull-mr](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Adevnull-mr+updated%3A2019-09-20..2020-03-31&type=Issues) | [@GeorgianaElena](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3AGeorgianaElena+updated%3A2019-09-20..2020-03-31&type=Issues) | [@jtpio](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Ajtpio+updated%3A2019-09-20..2020-03-31&type=Issues) | [@manics](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Amanics+updated%3A2019-09-20..2020-03-31&type=Issues) | [@muxator](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Amuxator+updated%3A2019-09-20..2020-03-31&type=Issues) | [@yuvipanda](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Ayuvipanda+updated%3A2019-09-20..2020-03-31&type=Issues)

## [0.1.4](https://github.com/jupyterhub/traefik-proxy/compare/0.1.3...0.1.4) 2019-09-20

## Merged PRs

- Add info about TraefikConsulProxy in readme [#80](https://github.com/jupyterhub/traefik-proxy/pull/80) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- Stop assuming kv_traefik_prefix ends with a slash [#79](https://github.com/jupyterhub/traefik-proxy/pull/79) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- Log info about what dynamic config file it's used by the Hub [#77](https://github.com/jupyterhub/traefik-proxy/pull/77) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- Install script [#76](https://github.com/jupyterhub/traefik-proxy/pull/76) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- Set defaults for traefik api username and password [#75](https://github.com/jupyterhub/traefik-proxy/pull/75) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- Allow etcd and consul client ssl settings [#70](https://github.com/jupyterhub/traefik-proxy/pull/70) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- Fix format in install script warnings [#69](https://github.com/jupyterhub/traefik-proxy/pull/69) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- Create test coverage report [#65](https://github.com/jupyterhub/traefik-proxy/pull/65) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- Explicitly close consul client session [#64](https://github.com/jupyterhub/traefik-proxy/pull/64) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- Throughput results updated [#62](https://github.com/jupyterhub/traefik-proxy/pull/62) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- Make trefik's log level configurable [#61](https://github.com/jupyterhub/traefik-proxy/pull/61) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- TraefikConsulProxy [#57](https://github.com/jupyterhub/traefik-proxy/pull/57) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- WIP Common proxy profiling suite [#54](https://github.com/jupyterhub/traefik-proxy/pull/54) ([@GeorgianaElena](https://github.com/GeorgianaElena))

## Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/traefik-proxy/graphs/contributors?from=2019-02-26&to=2019-09-20&type=c))

[@GeorgianaElena](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3AGeorgianaElena+updated%3A2019-02-26..2019-09-20&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Aminrk+updated%3A2019-02-26..2019-09-20&type=Issues)

## [0.1.3](https://github.com/jupyterhub/traefik-proxy/compare/0.1.2...0.1.3) 2019-02-26

- Load initial routing table from disk in TraefikTomlProxy when resuming from a previous session.

### Merged PRs

- Try to load routes from file if cache is empty [#52](https://github.com/jupyterhub/traefik-proxy/pull/52) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- close temporary file before renaming it [#51](https://github.com/jupyterhub/traefik-proxy/pull/51) ([@minrk](https://github.com/minrk))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/traefik-proxy/graphs/contributors?from=2019-02-22&to=2019-02-26&type=c))

[@GeorgianaElena](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3AGeorgianaElena+updated%3A2019-02-22..2019-02-26&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Aminrk+updated%3A2019-02-22..2019-02-26&type=Issues)

## [0.1.2](https://github.com/jupyterhub/traefik-proxy/compare/0.1.1...0.1.2) 2019-02-22

- Fix possible race in atomic_writing with TraefikTomlProxy

## [0.1.1](https://github.com/jupyterhub/traefik-proxy/compare/0.1.0...0.1.1) 2019-02-22

- make proxytest reusable with any Proxy implementation
- improve documentation
- improve logging and error handling
- make check_route_timeout configurable

### Merged PRs

- more logging / error handling [#49](https://github.com/jupyterhub/traefik-proxy/pull/49) ([@minrk](https://github.com/minrk))
- make check_route_timeout configurable [#48](https://github.com/jupyterhub/traefik-proxy/pull/48) ([@minrk](https://github.com/minrk))
- Update documentation and readme [#47](https://github.com/jupyterhub/traefik-proxy/pull/47) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- Define only the proxy fixture in test_proxy [#46](https://github.com/jupyterhub/traefik-proxy/pull/46) ([@GeorgianaElena](https://github.com/GeorgianaElena))
- add mocks so that test_check_routes needs only proxy fixture [#44](https://github.com/jupyterhub/traefik-proxy/pull/44) ([@minrk](https://github.com/minrk))
- Etcd with credentials [#43](https://github.com/jupyterhub/traefik-proxy/pull/43) ([@GeorgianaElena](https://github.com/GeorgianaElena))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/traefik-proxy/graphs/contributors?from=2019-02-19&to=2019-02-22&type=c))

[@GeorgianaElena](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3AGeorgianaElena+updated%3A2019-02-19..2019-02-22&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Aminrk+updated%3A2019-02-19..2019-02-22&type=Issues)

## 0.1.0

First release!
