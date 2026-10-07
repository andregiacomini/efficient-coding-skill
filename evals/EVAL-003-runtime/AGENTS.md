# Repository runtime

Use the supplied Python environment: `/opt/eval-003-venv/bin/python`.
Run repository tests with Django's runner and SQLite:

```sh
/opt/eval-003-venv/bin/python tests/runtests.py prefetch_related --settings=test_sqlite --parallel=1 --verbosity=2
```

For focused validation of the requested behavior:

```sh
/opt/eval-003-venv/bin/python tests/runtests.py prefetch_related.tests.PrefetchLimitTests --settings=test_sqlite --parallel=1 --verbosity=2
```

Dependencies are preinstalled. Python bytecode writing is disabled.
