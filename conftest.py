from typing import List

from playwright.sync_api import BrowserType

from src.fixtures.objects_fixture import *
from src.fixtures.user_fixtures import *
from src.fixtures.api_fixtures import *
from src.fixtures.visit_fixtures import *
from src.fixtures.setup_hook import *
from src.fixtures.assertion_fixtures.visit_assertion_fixtures import *
from src.fixtures.assertion_fixtures.patient_assertion_fixtures import *


import time
import random

from src.utils.browsers import norm_browser_name


def _apply_global_seed(seed: int) -> None:
    """
    Ensure deterministic random generation during test collection across xdist workers.

    This is critical when RandomData (and similar helpers) are called inside @pytest.mark.parametrize,
    because parametrization happens at import/collection time.
    """
    random.seed(seed)
    try:
        from faker import Faker
        Faker.seed(seed)
    except Exception:
        pass

    # Seed Faker instance used by our RandomData helper, if already imported.
    try:
        from src.api.generators import random_data
        if hasattr(random_data, "faker"):
            random_data.faker.seed_instance(seed)
    except Exception:
        pass

def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--seed",
        action="store",
        default=100, # move to env files later
        help="Seed for random generators. If not set, a new seed is generated per run (and shared across xdist workers).",
    )


def pytest_configure(config: pytest.Config) -> None:
    # In xdist workers, the master passes seed via workerinput.
    seed = None
    if hasattr(config, "workerinput"):
        seed = config.workerinput.get("seed")

    # In the master (or non-xdist runs), derive seed from CLI/env or generate a new one.
    if seed is None:
        opt = config.getoption("seed")
        seed = int(opt) if opt is not None else int(time.time_ns() % 2_000_000_000)

    config._openMRS_seed = int(seed)
    _apply_global_seed(int(seed))


def pytest_configure_node(node) -> None:
    # Pass the master seed to all workers so collection is identical.
    seed = getattr(node.config, "_openMRS_seed", None)
    if seed is not None:
        node.workerinput["seed"] = int(seed)

def pytest_collection_finish(session: pytest.Session) -> None:
    """
    IMPORTANT: avoid cross-worker data collisions in xdist.

    - We seed RNG in pytest_configure() to make COLLECTION deterministic (required for xdist),
      because @parametrize values may be generated at collection time.
    - After collection is finished, we reseed per worker for RUNTIME only, so workers don't
      generate identical usernames/passwords and clash on shared external resources.
    """
    config = session.config
    base_seed = getattr(config, "_openMRS_seed", None)
    if base_seed is None:
        return

    workerid = None
    if hasattr(config, "workerinput"):
        workerid = config.workerinput.get("workerid")

    if workerid and str(workerid).startswith("gw"):
        try:
            idx = int(str(workerid)[2:])
        except Exception:
            idx = 0
        runtime_seed = int(base_seed) + (idx + 1) * 1_000_000
    else:
        runtime_seed = int(base_seed)

    _apply_global_seed(runtime_seed)


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: List[pytest.Item],
):
    preferred = "chromium"

    filtered: List[pytest.Item] = []

    for item in items:
        is_ui = bool(item.get_closest_marker("ui"))
        fixts = getattr(item, "fixturenames", ())

        if (not is_ui) and ("browser_name" in fixts):
            callspec = getattr(item, "callspec", None)
            if callspec is not None and "browser_name" in callspec.params:
                bn = norm_browser_name(
                    callspec.params.get("browser_name")
                )
                if bn != preferred:
                    continue

        filtered.append(item)

    items[:] = filtered

@pytest.fixture(scope="session")
def browser_name(request):
    return request.config.getoption("--browser")

@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type: BrowserType):
    return {
        "headless": False,   # 👈 ВАЖНО
        "slow_mo": 300,      # 👈 необязательно, но очень помогает
    }