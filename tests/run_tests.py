"""Dependency-free test runner for ChitChat.

The suite is written in plain pytest style (``Test*`` classes, ``test_*``
methods, ``setup_method`` / ``setup_class`` hooks, bare ``assert``).  The
tests deliberately need no fixtures, so this runner executes the exact
same tests without requiring pytest to be installed:

    python tests/run_tests.py            # run everything
    python tests/run_tests.py store      # only files matching "store"

If pytest *is* available, ``python -m pytest`` works too.
"""

import importlib.util
import os
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.join(ROOT, "tests")
sys.path.insert(0, ROOT)


def _load_module(path: str):
    name = "chitchat_test_" + os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_callable(fn, results, label):
    try:
        fn()
    except Exception:
        results["failed"] += 1
        results["failures"].append((label, traceback.format_exc()))
    else:
        results["passed"] += 1
        print(f"  PASS  {label}")


def run_module(module, results):
    # Module-level test functions
    for attr in sorted(dir(module)):
        if attr.startswith("test_") and callable(getattr(module, attr)):
            _run_callable(getattr(module, attr), results, attr)

    # Test classes
    for cls_name in sorted(dir(module)):
        if not cls_name.startswith("Test"):
            continue
        cls = getattr(module, cls_name)
        if not isinstance(cls, type):
            continue
        methods = [m for m in sorted(dir(cls))
                   if m.startswith("test_") and callable(getattr(cls, m))]
        if not methods:
            continue
        setup_class = getattr(cls, "setup_class", None)
        teardown_class = getattr(cls, "teardown_class", None)
        if setup_class:
            try:
                setup_class()
            except Exception:
                results["failed"] += 1
                results["failures"].append(
                    (f"{cls_name}.setup_class", traceback.format_exc()))
                continue
        try:
            for method_name in methods:
                instance = cls()
                setup = getattr(instance, "setup_method", None)
                teardown = getattr(instance, "teardown_method", None)
                if setup:
                    try:
                        setup()
                    except Exception:
                        results["failed"] += 1
                        results["failures"].append(
                            (f"{cls_name}.{method_name}.setup_method",
                             traceback.format_exc()))
                        continue
                try:
                    _run_callable(getattr(instance, method_name), results,
                                  f"{cls_name}.{method_name}")
                finally:
                    if teardown:
                        try:
                            teardown()
                        except Exception:
                            pass
        finally:
            if teardown_class:
                try:
                    teardown_class()
                except Exception:
                    pass


def main(argv):
    selector = argv[1] if len(argv) > 1 else ""
    files = sorted(
        f for f in os.listdir(TESTS_DIR)
        if f.startswith("test_") and f.endswith(".py") and selector in f
    )
    if not files:
        print(f"No test files matched {selector!r}")
        return 1

    results = {"passed": 0, "failed": 0, "failures": []}
    for filename in files:
        path = os.path.join(TESTS_DIR, filename)
        print(f"\n{filename}")
        try:
            module = _load_module(path)
        except Exception:
            results["failed"] += 1
            results["failures"].append((filename, traceback.format_exc()))
            print("  ERROR importing module")
            continue
        run_module(module, results)

    total = results["passed"] + results["failed"]
    print("\n" + "=" * 60)
    if results["failures"]:
        print("FAILURES")
        print("=" * 60)
        for label, tb in results["failures"]:
            print(f"\n--- {label} ---")
            print(tb.rstrip())
        print()
    print(f"{results['passed']}/{total} passed, {results['failed']} failed")
    return 0 if results["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
