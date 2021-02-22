.. _changelog:

Changelog
=========

For detailed changes from the prior release, click on the version number
and its link will bring up a GitHub listing of changes. Use `git log` on
the command line for details.

`[0.1.6]`_ - 2020-05-16
-----------------------

-  Fix circular reference error `#107`_
   `(@GeorgianaElena) <https://github.com/GeorgianaElena>`_
-  Fix TypeError: 'NoneType' object is not iterable, in
   delete_route when route doesn't exist `#104`_
   `(@mofanke) <https://github.com/mofanke>`_
-  Update etcd.py `#102`_ `(@mofanke) <https://github.com/mofanke>`_
-  New Proxy config option traefik_api_validate_cert `#98`_
   `(@devnull-mr) <https://github.com/devnull-mr>`_

.. _#107: https://github.com/jupyterhub/traefik-proxy/pull/107
.. _#104: https://github.com/jupyterhub/traefik-proxy/pull/104
.. _#102: https://github.com/jupyterhub/traefik-proxy/pull/102
.. _#98: https://github.com/jupyterhub/traefik-proxy/pull/98


`[0.1.5]`_ - 2020-03-31
-----------------------

-  Fix named servers routing `#96`_
   `(@GeorgianaElena) <https://github.com/GeorgianaElena>`_
-  Show a message when no binary is provided to the installer `#95`_
   `(@GeorgianaElena) <https://github.com/GeorgianaElena>`_
-  Update install utility docs `#93`_
   `(@jtpio) <https://github.com/jtpio>`_
-  Travis deploy tags to PyPI `#89`_
   `(@GeorgianaElena) <https://github.com/GeorgianaElena>`_
-  Update README `#87`_
   (`@consideRatio <https://github.com/consideRatio>`_)
-  Handle ssl `#84`_
   `(@GeorgianaElena) <https://github.com/GeorgianaElena>`_
-  CONTRIBUTING: use long option in “pip install -e” `#82`_
   (`@muxator <https://github.com/muxator>`_)
-  Change traefik default version `#81`_
   `(@GeorgianaElena) <https://github.com/GeorgianaElena>`_
-  Add info about TraefikConsulProxy in readme `#80`_
   `(@GeorgianaElena) <https://github.com/GeorgianaElena>`_

.. _#96: https://github.com/jupyterhub/traefik-proxy/pull/96
.. _#95: https://github.com/jupyterhub/traefik-proxy/pull/95
.. _#93: https://github.com/jupyterhub/traefik-proxy/pull/93
.. _#89: https://github.com/jupyterhub/traefik-proxy/pull/89
.. _#87: https://github.com/jupyterhub/traefik-proxy/pull/87
.. _#84: https://github.com/jupyterhub/traefik-proxy/pull/84
.. _#82: https://github.com/jupyterhub/traefik-proxy/pull/82
.. _#81: https://github.com/jupyterhub/traefik-proxy/pull/81
.. _#80: https://github.com/jupyterhub/traefik-proxy/pull/80

`[0.1.4]`_ - 2019-09-20
-----------------------

-  Add info about TraefikConsulProxy in readme `#80`_
   `(@GeorgianaElena) <https://github.com/GeorgianaElena>`_
-  Stop assuming kv_traefik_prefix ends with a slash `#79`_
   `(@GeorgianaElena) <https://github.com/GeorgianaElena>`_
-  Log info about what dynamic config file it’s used by the Hub `#77`_
   `(@GeorgianaElena) <https://github.com/GeorgianaElena>`_
-  Install script `#76`_
   `(@GeorgianaElena) <https://github.com/GeorgianaElena>`_
-  Set defaults for traefik api username and password `#75`_
   `(@GeorgianaElena) <https://github.com/GeorgianaElena>`_
-  Allow etcd and consul client ssl settings `#70`_
   `(@GeorgianaElena) <https://github.com/GeorgianaElena>`_
-  Fix format in install script warnings `#69`_
   `(@GeorgianaElena) <https://github.com/GeorgianaElena>`_
-  Create test coverage report `#65`_
   `(@GeorgianaElena) <https://github.com/GeorgianaElena>`_
-  Explicitly close consul client session `#64`_
   `(@GeorgianaElena) <https://github.com/GeorgianaElena>`_
-  Throughput results updated `#62`_
   `(@GeorgianaElena) <https://github.com/GeorgianaElena>`_
-  Make trefik’s log level configurable `#61`_
   `(@GeorgianaElena) <https://github.com/GeorgianaElena>`_
-  TraefikConsulProxy `#57`_
   `(@GeorgianaElena) <https://github.com/GeorgianaElena>`_
-  WIP Common proxy profiling suite `#54`_
   `(@GeorgianaElena) <https://github.com/GeorgianaElena>`_

.. _#80: https://github.com/jupyterhub/traefik-proxy/pull/80
.. _#79: https://github.com/jupyterhub/traefik-proxy/pull/79
.. _#77: https://github.com/jupyterhub/traefik-proxy/pull/77
.. _#76: https://github.com/jupyterhub/traefik-proxy/pull/76
.. _#75: https://github.com/jupyterhub/traefik-proxy/pull/75
.. _#70: https://github.com/jupyterhub/traefik-proxy/pull/70
.. _#69: https://github.com/jupyterhub/traefik-proxy/pull/69
.. _#65: https://github.com/jupyterhub/traefik-proxy/pull/65
.. _#64: https://github.com/jupyterhub/traefik-proxy/pull/64
.. _#62: https://github.com/jupyterhub/traefik-proxy/pull/62
.. _#61: https://github.com/jupyterhub/traefik-proxy/pull/61
.. _#57: https://github.com/jupyterhub/traefik-proxy/pull/57
.. _#54: https://github.com/jupyterhub/traefik-proxy/pull/54

`[0.1.3]`_ - 2019-02-26
-----------------------

-  Load initial routing table from disk in TraefikTomlProxy
   when resuming from a previous session.

**Details:**

-  Try to load routes from file if cache is empty `#52`_
   (`@GeorgianaElena <https://github.com/GeorgianaElena>`_)
-  close temporary file before renaming it `#51`_
   (`@minrk <https://github.com/minrk>`_)

.. _#52: https://github.com/jupyterhub/traefik-proxy/pull/52
.. _#51: https://github.com/jupyterhub/traefik-proxy/pull/51


`[0.1.2]`_ - 2019-02-22
-----------------------

- Fix possible race in atomic_writing with TraefikTomlProxy

`[0.1.1]`_ - 2019-02-22
-----------------------

- make proxytest reusable with any Proxy implementation
- improve documentation
- improve logging and error handling
- make check_route_timeout configurable

**Details:**

-  more logging / error handling `#49`_
   (`@minrk <https://github.com/minrk>`_)
-  make check_route_timeout configurable `#48`_
   (`@minrk <https://github.com/minrk>`_)
-  Update documentation and readme `#47`_
   (`@GeorgianaElena <https://github.com/GeorgianaElena>`_)
-  Define only the proxy fixture in test_proxy `#46`_
   (`@GeorgianaElena <https://github.com/GeorgianaElena>`_)
-  add mocks so that test_check_routes needs only proxy fixture `#44`_
   (`@minrk <https://github.com/minrk>`_)
-  Etcd with credentials `#43`_
   (`@GeorgianaElena <https://github.com/GeorgianaElena>`_)

.. _#49: https://github.com/jupyterhub/traefik-proxy/pull/49
.. _#48: https://github.com/jupyterhub/traefik-proxy/pull/48
.. _#47: https://github.com/jupyterhub/traefik-proxy/pull/47
.. _#46: https://github.com/jupyterhub/traefik-proxy/pull/46
.. _#44: https://github.com/jupyterhub/traefik-proxy/pull/44
.. _#43: https://github.com/jupyterhub/traefik-proxy/pull/43


0.1.0
-----

First release!

.. _[0.1.6]: https://github.com/jupyterhub/traefik-proxy/compare/0.1.5...0.1.6
.. _[0.1.5]: https://github.com/jupyterhub/traefik-proxy/compare/0.1.4...0.1.5
.. _[0.1.4]: https://github.com/jupyterhub/traefik-proxy/compare/0.1.3...0.1.4
.. _[0.1.3]: https://github.com/jupyterhub/traefik-proxy/compare/0.1.2...0.1.3
.. _[0.1.2]: https://github.com/jupyterhub/traefik-proxy/compare/0.1.1...0.1.2
.. _[0.1.1]: https://github.com/jupyterhub/traefik-proxy/compare/0.1.0...0.1.1
.. _[Unreleased]: https://github.com/jupyterhub/traefik-proxy/compare/0.1.4...2e96af5861f717a136ea76919dfab585643642fa