========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |appveyor| |requires|
        | |codecov|
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|

.. |docs| image:: https://readthedocs.org/projects/pybfx/badge/?style=flat
    :target: https://readthedocs.org/projects/pybfx
    :alt: Documentation Status

.. |travis| image:: https://travis-ci.org/pmav99/pybfx.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/pmav99/pybfx

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/pmav99/pybfx?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/pmav99/pybfx

.. |requires| image:: https://requires.io/github/pmav99/pybfx/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/pmav99/pybfx/requirements/?branch=master

.. |codecov| image:: https://codecov.io/github/pmav99/pybfx/coverage.svg?branch=master
    :alt: Coverage Status
    :target: https://codecov.io/github/pmav99/pybfx

.. |version| image:: https://img.shields.io/pypi/v/pybfx.svg
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/pybfx

.. |commits-since| image:: https://img.shields.io/github/commits-since/pmav99/pybfx/v0.2.0.svg
    :alt: Commits since latest release
    :target: https://github.com/pmav99/pybfx/compare/v0.2.0...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/pybfx.svg
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/pybfx

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/pybfx.svg
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/pybfx

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/pybfx.svg
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/pybfx


.. end-badges

A library for the Bitfinex API

* Free software: BSD 3-Clause License

Installation
============

::

    pip install pybfx

Documentation
=============

https://pybfx.readthedocs.io/

Development
===========

To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
