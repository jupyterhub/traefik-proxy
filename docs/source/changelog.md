# Changelog

## 2.1.0 2025-03-28

([full changelog](https://github.com/jupyterhub/traefik-proxy/compare/2.0.0...2.1.0))

### New features added

- allow explicit traefik_api_hashed_password, use bcrypt for hash instead of md5 [#269](https://github.com/jupyterhub/traefik-proxy/pull/269) ([@minrk](https://github.com/minrk), [@manics](https://github.com/manics))

### Maintenance and upkeep improvements

- update tests for websockets 14, python 3.13 ssl [#268](https://github.com/jupyterhub/traefik-proxy/pull/268) ([@minrk](https://github.com/minrk))
- ignore some more files [#267](https://github.com/jupyterhub/traefik-proxy/pull/267) ([@minrk](https://github.com/minrk))
- Bump default traefik version to install from 2.10.7 to 3.1.4 [#258](https://github.com/jupyterhub/traefik-proxy/pull/258) ([@consideRatio](https://github.com/consideRatio), [@minrk](https://github.com/minrk))

### Documentation improvements

- add missing example redis config [#261](https://github.com/jupyterhub/traefik-proxy/pull/261) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena))
- Fix link to traefik example [#260](https://github.com/jupyterhub/traefik-proxy/pull/260) ([@matuzalemmuller](https://github.com/matuzalemmuller), [@manics](https://github.com/manics), [@minrk](https://github.com/minrk))
- Update Docs on setting up https [#254](https://github.com/jupyterhub/traefik-proxy/pull/254) ([@buti1021](https://github.com/buti1021), [@minrk](https://github.com/minrk))

### Contributors to this release

The following people contributed discussions, new ideas, code and documentation contributions, and review.
See [our definition of contributors](https://github-activity.readthedocs.io/en/latest/#how-does-this-tool-define-contributions-in-the-reports).

([GitHub contributors page for this release](https://github.com/jupyterhub/traefik-proxy/graphs/contributors?from=2024-08-22&to=2025-03-27&type=c))

@buti1021 ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Abuti1021+updated%3A2024-08-22..2025-03-27&type=Issues)) | @consideRatio ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3AconsideRatio+updated%3A2024-08-22..2025-03-27&type=Issues)) | @GeorgianaElena ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3AGeorgianaElena+updated%3A2024-08-22..2025-03-27&type=Issues)) | @manics ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Amanics+updated%3A2024-08-22..2025-03-27&type=Issues)) | @matuzalemmuller ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Amatuzalemmuller+updated%3A2024-08-22..2025-03-27&type=Issues)) | @minrk ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Aminrk+updated%3A2024-08-22..2025-03-27&type=Issues)) | @rcthomas ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Arcthomas+updated%3A2024-08-22..2025-03-27&type=Issues))

### Contributors to this release

The following people contributed discussions, new ideas, code and documentation contributions, and review.
See [our definition of contributors](https://github-activity.readthedocs.io/en/latest/#how-does-this-tool-define-contributions-in-the-reports).

([GitHub contributors page for this release](https://github.com/jupyterhub/traefik-proxy/graphs/contributors?from=2024-08-22&to=2025-03-27&type=c))

@buti1021 ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Abuti1021+updated%3A2024-08-22..2025-03-27&type=Issues)) | @consideRatio ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3AconsideRatio+updated%3A2024-08-22..2025-03-27&type=Issues)) | @GeorgianaElena ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3AGeorgianaElena+updated%3A2024-08-22..2025-03-27&type=Issues)) | @manics ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Amanics+updated%3A2024-08-22..2025-03-27&type=Issues)) | @matuzalemmuller ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Amatuzalemmuller+updated%3A2024-08-22..2025-03-27&type=Issues)) | @minrk ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Aminrk+updated%3A2024-08-22..2025-03-27&type=Issues)) | @rcthomas ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Arcthomas+updated%3A2024-08-22..2025-03-27&type=Issues))

## 2.0.0 2024-08-22

([full changelog](https://github.com/jupyterhub/traefik-proxy/compare/1.1.0...2.0.0))

### API and Breaking Changes

- Require python 3.8+ [#232](https://github.com/jupyterhub/traefik-proxy/pull/232) ([@consideRatio](https://github.com/consideRatio), [@minrk](https://github.com/minrk))

### New features added

- add redis implementation [#230](https://github.com/jupyterhub/traefik-proxy/pull/230) ([@minrk](https://github.com/minrk), [@consideRatio](https://github.com/consideRatio), [@GeorgianaElena](https://github.com/GeorgianaElena), [@manics](https://github.com/manics))
- Add arm64 support to install script [#220](https://github.com/jupyterhub/traefik-proxy/pull/220) ([@cmd-ntrf](https://github.com/cmd-ntrf), [@minrk](https://github.com/minrk))

### Enhancements made

- [redis] add default retry config [#244](https://github.com/jupyterhub/traefik-proxy/pull/244) ([@minrk](https://github.com/minrk), [@consideRatio](https://github.com/consideRatio))

## Bugs fixed

- fix initial cursor in delete script [#253](https://github.com/jupyterhub/traefik-proxy/pull/253) ([@minrk](https://github.com/minrk))

### Maintenance and upkeep improvements

- Update default traefik to install to 2.10.7 [#233](https://github.com/jupyterhub/traefik-proxy/pull/233) ([@consideRatio](https://github.com/consideRatio), [@minrk](https://github.com/minrk))
- Test python 3.12, redis 7, traefik 3 - and misc updates to align with jupyterhub-python-repo-template [#231](https://github.com/jupyterhub/traefik-proxy/pull/231) ([@consideRatio](https://github.com/consideRatio), [@GeorgianaElena](https://github.com/GeorgianaElena), [@minrk](https://github.com/minrk))
- temporary pin for pytest-asyncio [#227](https://github.com/jupyterhub/traefik-proxy/pull/227) ([@minrk](https://github.com/minrk), [@consideRatio](https://github.com/consideRatio))

### Documentation improvements

- Note keyspace notifications, persistence requirement for redis [#246](https://github.com/jupyterhub/traefik-proxy/pull/246) ([@minrk](https://github.com/minrk), [@consideRatio](https://github.com/consideRatio))
- Express yaml optional dependency [#245](https://github.com/jupyterhub/traefik-proxy/pull/245) ([@minrk](https://github.com/minrk), [@consideRatio](https://github.com/consideRatio))
- README: Emphasize Redis over Etcd and Consul [#243](https://github.com/jupyterhub/traefik-proxy/pull/243) ([@manics](https://github.com/manics), [@minrk](https://github.com/minrk))

### Continuous integration improvements

- ci: test with traefik v3.0.0 [#240](https://github.com/jupyterhub/traefik-proxy/pull/240) ([@consideRatio](https://github.com/consideRatio))
- ci: test with traefik v2.11.2 and v3.0.0-rc5 [#239](https://github.com/jupyterhub/traefik-proxy/pull/239) ([@consideRatio](https://github.com/consideRatio))
- Bump codecov/codecov-action from 3 to 4 [#234](https://github.com/jupyterhub/traefik-proxy/pull/234) ([@consideRatio](https://github.com/consideRatio))
- Bump actions/setup-python from 4 to 5 [#225](https://github.com/jupyterhub/traefik-proxy/pull/225) ([@consideRatio](https://github.com/consideRatio))
- Bump actions/checkout from 3 to 4 [#221](https://github.com/jupyterhub/traefik-proxy/pull/221) ([@consideRatio](https://github.com/consideRatio))
- Bump pypa/gh-action-pypi-publish from 1.8.6 to release/v1 (edited) [#214](https://github.com/jupyterhub/traefik-proxy/pull/214) ([@consideRatio](https://github.com/consideRatio))

### Contributors to this release

The following people contributed discussions, new ideas, code and documentation contributions, and review.
See [our definition of contributors](https://github-activity.readthedocs.io/en/latest/#how-does-this-tool-define-contributions-in-the-reports).

([GitHub contributors page for this release](https://github.com/jupyterhub/traefik-proxy/graphs/contributors?from=2023-06-06&to=2024-08-22&type=c))

[@cmd-ntrf](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Acmd-ntrf+updated%3A2023-06-06..2024-08-22&type=Issues) | [@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3AconsideRatio+updated%3A2023-06-06..2024-08-22&type=Issues) | [@dependabot](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Adependabot+updated%3A2023-06-06..2024-08-22&type=Issues) | [@manics](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Amanics+updated%3A2023-06-06..2024-08-22&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Aminrk+updated%3A2023-06-06..2024-08-22&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Apre-commit-ci+updated%3A2023-06-06..2024-08-22&type=Issues) | [@rcthomas](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Arcthomas+updated%3A2023-06-06..2024-08-22&type=Issues) | [@welcome](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Awelcome+updated%3A2023-06-06..2024-08-22&type=Issues)

## 1.1.0 - 2023-06-06

([full changelog](https://github.com/jupyterhub/traefik-proxy/compare/1.0.1...1.1.0))

### New features added

- add TraefikProxy.enable_setup_dynamic_config for opt-out of dynamic config setup [#210](https://github.com/jupyterhub/traefik-proxy/pull/210) ([@minrk](https://github.com/minrk), [@alexleach](https://github.com/alexleach))

### Contributors to this release

The following people contributed discussions, new ideas, code and documentation contributions, and review.
See [our definition of contributors](https://github-activity.readthedocs.io/en/latest/#how-does-this-tool-define-contributions-in-the-reports).

([GitHub contributors page for this release](https://github.com/jupyterhub/traefik-proxy/graphs/contributors?from=2023-05-25&to=2023-06-02&type=c))

@alexleach ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Aalexleach+updated%3A2023-05-25..2023-06-02&type=Issues)) | @consideRatio ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3AconsideRatio+updated%3A2023-05-25..2023-06-02&type=Issues)) | @minrk ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Aminrk+updated%3A2023-05-25..2023-06-02&type=Issues))

## 1.0.1 - 2023-05-25

1.0.1 fixes some packing issues in the 1.0 release.
No changes to actual behavior.

([full changelog](https://github.com/jupyterhub/traefik-proxy/compare/1.0.0...1.0.1))

### Maintenance and upkeep improvements

- ensure `requirements.txt` is included in the sdist, exclude `performance` and importable `tests` [#207](https://github.com/jupyterhub/traefik-proxy/pull/207) ([@bollwyvl](https://github.com/bollwyvl), [@minrk](https://github.com/minrk))

### Contributors to this release

The following people contributed discussions, new ideas, code and documentation contributions, and review.
See [our definition of contributors](https://github-activity.readthedocs.io/en/latest/#how-does-this-tool-define-contributions-in-the-reports).

([GitHub contributors page for this release](https://github.com/jupyterhub/traefik-proxy/graphs/contributors?from=2023-05-16&to=2023-05-25&type=c))

@bollwyvl ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Abollwyvl+updated%3A2023-05-16..2023-05-25&type=Issues)) | @minrk ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Aminrk+updated%3A2023-05-16..2023-05-25&type=Issues))

## 1.0.0 - 2023-05-16

1.0.0 is a big release for jupyterhub-traefik-proxy!
It updates support for traefik to version 2.x (current default: 2.10.1).
Traefik versions < 2.0 are no longer supported.
If you have custom traefik configuration,
make sure to checkout [traefik's v1 to v2 migration guide](https://doc.traefik.io/traefik/migration/v1-to-v2/),
since your configuration may need updating.

A major consequence of the v2 updates is that the performance of adding and removing routes when there are a large number already defined is now greatly improved,
and no longer grows significantly with the number of routes.

Major changes:

- Traefik v2 is required. Traefik v1 is not supported.
- `TraefikTomlProxy` is deprecated in favor of `TraefikFileProviderProxy`,
  which supports both toml and yaml.
  Replace `traefik_toml` with `traefik_file` in your configuration.
- `python3 -m jupyterhub_traefik_proxy.install` will now only install traefik, not any key-value-store providers.
  You can follow your KV store's own installation instructions.
- `python3 -m jupyterhub_traefik_proxy.install --traefik-version x.y.z` now supports fetching any published traefik version on any architecture,
  instead of a few preset versions.

Performance and responsiveness is also greatly improved.

([full changelog](https://github.com/jupyterhub/traefik-proxy/compare/0.3.0...1.0.0))

### API and Breaking Changes

- remove kv stores from install.py [#156](https://github.com/jupyterhub/traefik-proxy/pull/156) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena), [@consideRatio](https://github.com/consideRatio))
- Traefik v2 support [#145](https://github.com/jupyterhub/traefik-proxy/pull/145) ([@GeorgianaElena](https://github.com/GeorgianaElena), [@minrk](https://github.com/minrk), [@alexleach](https://github.com/alexleach))

### New features added

- Traefik v2 support [#145](https://github.com/jupyterhub/traefik-proxy/pull/145) ([@GeorgianaElena](https://github.com/GeorgianaElena), [@minrk](https://github.com/minrk), [@alexleach](https://github.com/alexleach))

### Enhancements made

- update default bootstrapped traefik to 2.10.1 [#206](https://github.com/jupyterhub/traefik-proxy/pull/206) ([@minrk](https://github.com/minrk), [@consideRatio](https://github.com/consideRatio))
- simplify ssl, passthrough configuration [#199](https://github.com/jupyterhub/traefik-proxy/pull/199) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena))
- reduce requirements of KV store implementations and custom methods [#185](https://github.com/jupyterhub/traefik-proxy/pull/185) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena))
- Improve performance, scaling [#165](https://github.com/jupyterhub/traefik-proxy/pull/165) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena))
- Improve error message on traefik api access error [#140](https://github.com/jupyterhub/traefik-proxy/pull/140) ([@twalcari](https://github.com/twalcari), [@minrk](https://github.com/minrk))

### Bugs fixed

- make sure that `/prefix` and `/prefix/` are handled the same [#197](https://github.com/jupyterhub/traefik-proxy/pull/197) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena), [@manics](https://github.com/manics))
- Fix handling of empty dicts in traefik config [#173](https://github.com/jupyterhub/traefik-proxy/pull/173) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena))

### Maintenance and upkeep improvements

- dependabot: monthly updates of github actions [#201](https://github.com/jupyterhub/traefik-proxy/pull/201) ([@consideRatio](https://github.com/consideRatio))
- trade versioneer for tbump [#193](https://github.com/jupyterhub/traefik-proxy/pull/193) ([@minrk](https://github.com/minrk), [@consideRatio](https://github.com/consideRatio))
- make api endpoint configurable, restore previous entrypoint names [#192](https://github.com/jupyterhub/traefik-proxy/pull/192) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena))
- set providersThrottleDuration=0s in tests [#190](https://github.com/jupyterhub/traefik-proxy/pull/190) ([@minrk](https://github.com/minrk), [@consideRatio](https://github.com/consideRatio))
- fix heading level in 0.3 changelog [#188](https://github.com/jupyterhub/traefik-proxy/pull/188) ([@minrk](https://github.com/minrk))
- run rst2md on remaining rst files [#187](https://github.com/jupyterhub/traefik-proxy/pull/187) ([@minrk](https://github.com/minrk))
- use editable install to get test coverage [#186](https://github.com/jupyterhub/traefik-proxy/pull/186) ([@minrk](https://github.com/minrk))
- Make traefik_entrypoint name explicit [#184](https://github.com/jupyterhub/traefik-proxy/pull/184) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena))
- test: fix consul auth port [#183](https://github.com/jupyterhub/traefik-proxy/pull/183) ([@minrk](https://github.com/minrk), [@consideRatio](https://github.com/consideRatio), [@GeorgianaElena](https://github.com/GeorgianaElena))
- deprecate consul due to unhealthy API clients [#182](https://github.com/jupyterhub/traefik-proxy/pull/182) ([@minrk](https://github.com/minrk), [@consideRatio](https://github.com/consideRatio))
- add dependabot config for github actions [#178](https://github.com/jupyterhub/traefik-proxy/pull/178) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena))
- reuse backends across tests [#174](https://github.com/jupyterhub/traefik-proxy/pull/174) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena))
- simplify some test fixtures [#169](https://github.com/jupyterhub/traefik-proxy/pull/169) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena))
- avoid deprecation warning in `--slow-last` sorting [#168](https://github.com/jupyterhub/traefik-proxy/pull/168) ([@minrk](https://github.com/minrk))
- restore proxy tests [#167](https://github.com/jupyterhub/traefik-proxy/pull/167) ([@minrk](https://github.com/minrk), [@manics](https://github.com/manics))
- Minor cleanup of start/stop methods and logging [#166](https://github.com/jupyterhub/traefik-proxy/pull/166) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena))
- Respect ip address config in urls, don't serve dashboard by default [#162](https://github.com/jupyterhub/traefik-proxy/pull/162) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena), [@consideRatio](https://github.com/consideRatio))
- minor logging tweaks [#161](https://github.com/jupyterhub/traefik-proxy/pull/161) ([@minrk](https://github.com/minrk), [@consideRatio](https://github.com/consideRatio))
- Use checksums from traefik releases [#160](https://github.com/jupyterhub/traefik-proxy/pull/160) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena))
- Add pre-commit config and configure autoformating tools and pytest from pyproject.toml [#157](https://github.com/jupyterhub/traefik-proxy/pull/157) ([@GeorgianaElena](https://github.com/GeorgianaElena), [@minrk](https://github.com/minrk), [@consideRatio](https://github.com/consideRatio))
- Deprecations for v2 upgrades [#154](https://github.com/jupyterhub/traefik-proxy/pull/154) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena), [@alexleach](https://github.com/alexleach), [@consideRatio](https://github.com/consideRatio))
- switch etcd3 client for Python 3.11 support [#153](https://github.com/jupyterhub/traefik-proxy/pull/153) ([@minrk](https://github.com/minrk), [@consideRatio](https://github.com/consideRatio))
- Support External Traefik Certificate Resolver and update grpc [#152](https://github.com/jupyterhub/traefik-proxy/pull/152) ([@alexleach](https://github.com/alexleach), [@minrk](https://github.com/minrk))
- improve test time [#150](https://github.com/jupyterhub/traefik-proxy/pull/150) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena))
- Get the repo back running [#144](https://github.com/jupyterhub/traefik-proxy/pull/144) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena), [@consideRatio](https://github.com/consideRatio))
- prepare to rename default branch to main [#143](https://github.com/jupyterhub/traefik-proxy/pull/143) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena))

### Documentation improvements

- add document on enabling https [#204](https://github.com/jupyterhub/traefik-proxy/pull/204) ([@minrk](https://github.com/minrk), [@consideRatio](https://github.com/consideRatio))
- update changelog for 1.0.0b2 [#194](https://github.com/jupyterhub/traefik-proxy/pull/194) ([@minrk](https://github.com/minrk))
- doc: update sample configuration for v2 [#189](https://github.com/jupyterhub/traefik-proxy/pull/189) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena))
- Fix CI README badges [#177](https://github.com/jupyterhub/traefik-proxy/pull/177) ([@manics](https://github.com/manics), [@consideRatio](https://github.com/consideRatio))
- changelog for 1.0 [#176](https://github.com/jupyterhub/traefik-proxy/pull/176) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena), [@manics](https://github.com/manics))
- docs: update link to traefik API [#175](https://github.com/jupyterhub/traefik-proxy/pull/175) ([@minrk](https://github.com/minrk), [@manics](https://github.com/manics))
- Update performance benchmarks for v2 [#163](https://github.com/jupyterhub/traefik-proxy/pull/163) ([@minrk](https://github.com/minrk), [@GeorgianaElena](https://github.com/GeorgianaElena), [@manics](https://github.com/manics))
- Revert some entrypoint names in docs, renumber how to install steps [#196](https://github.com/jupyterhub/traefik-proxy/pull/196) ([@rcthomas](https://github.com/rcthomas), [@GeorgianaElena](https://github.com/GeorgianaElena))

### Contributors to this release

The following people contributed discussions, new ideas, code and documentation contributions, and review.
See [our definition of contributors](https://github-activity.readthedocs.io/en/latest/#how-does-this-tool-define-contributions-in-the-reports).

([GitHub contributors page for this release](https://github.com/jupyterhub/traefik-proxy/graphs/contributors?from=2021-10-18&to=2023-05-16&type=c))

@alexleach ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Aalexleach+updated%3A2021-10-18..2023-05-16&type=Issues)) | @consideRatio ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3AconsideRatio+updated%3A2021-10-18..2023-05-16&type=Issues)) | @dependabot ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Adependabot+updated%3A2021-10-18..2023-05-16&type=Issues)) | @devnull-mr ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Adevnull-mr+updated%3A2021-10-18..2023-05-16&type=Issues)) | @dolfinus ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Adolfinus+updated%3A2021-10-18..2023-05-16&type=Issues)) | @GeorgianaElena ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3AGeorgianaElena+updated%3A2021-10-18..2023-05-16&type=Issues)) | @manics ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Amanics+updated%3A2021-10-18..2023-05-16&type=Issues)) | @maulikjs ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Amaulikjs+updated%3A2021-10-18..2023-05-16&type=Issues)) | @minrk ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Aminrk+updated%3A2021-10-18..2023-05-16&type=Issues)) | @pre-commit-ci ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Apre-commit-ci+updated%3A2021-10-18..2023-05-16&type=Issues)) | @rcthomas ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Arcthomas+updated%3A2021-10-18..2023-05-16&type=Issues)) | @twalcari ([activity](https://github.com/search?q=repo%3Ajupyterhub%2Ftraefik-proxy+involves%3Atwalcari+updated%3A2021-10-18..2023-05-16&type=Issues))

## [0.3.0](https://github.com/jupyterhub/traefik-proxy/compare/0.2.0...0.3.0) 2021-10-18

### Enhancements made

- Support ARM in binary package installs [#129](https://github.com/jupyterhub/traefik-proxy/pull/129) ([@yuvipanda](https://github.com/yuvipanda))

### Bugs fixed

- Fix handling default server routes in TraefikTomlProxy [#131](https://github.com/jupyterhub/traefik-proxy/pull/131) ([@dolfinus](https://github.com/dolfinus))
- Make etcd3 & python-consul2 soft dependencies [#127](https://github.com/jupyterhub/traefik-proxy/pull/127) ([@yuvipanda](https://github.com/yuvipanda))

### Continuous integration

- ci: don't run tests if docs change [#139](https://github.com/jupyterhub/traefik-proxy/pull/139) ([@consideRatio](https://github.com/consideRatio))
- ci/docs: install autodocs-traits as a PyPI package & pin sphinx [#138](https://github.com/jupyterhub/traefik-proxy/pull/138) ([@consideRatio](https://github.com/consideRatio))

### Contributors to this release

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
