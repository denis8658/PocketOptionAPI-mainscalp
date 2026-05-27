import asyncio
import inspect


def pytest_pyfunc_call(pyfuncitem):
    """Run async test functions even when pytest-asyncio is unavailable."""
    testfunction = pyfuncitem.obj
    if not inspect.iscoroutinefunction(testfunction):
        return None

    fixture_names = pyfuncitem._fixtureinfo.argnames
    testargs = {name: pyfuncitem.funcargs[name] for name in fixture_names}
    asyncio.run(testfunction(**testargs))
    return True
