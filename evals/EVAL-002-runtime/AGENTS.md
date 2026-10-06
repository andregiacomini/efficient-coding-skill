# Benchmark runtime

Python and test dependencies are installed in `/opt/eval-venv`.
Run the relevant regression test with:

```sh
/opt/eval-venv/bin/python -m pytest -q test/execution_summary_test.py::ExecutionSummaryTest::test_status_with_task_retry
```

The benchmark-provided tests are available in this repository.
