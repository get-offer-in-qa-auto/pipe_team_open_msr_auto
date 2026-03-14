import hashlib
import logging
import random
import re
import time
from pathlib import Path
from typing import List

from playwright.sync_api import BrowserType

from src.api.coverage.api_coverage_collector import ApiCoverageCollector
from src.api.coverage.calculate_api_coverage import calculate_and_save_summary
from src.api.coverage.swagger_operations import generate_swagger_operations
from src.fixtures.api_fixtures import *  # noqa: F403
from src.fixtures.assertion_fixtures.patient_assertion_fixtures import *  # noqa: F403
from src.fixtures.assertion_fixtures.visit_assertion_fixtures import *  # noqa: F403
from src.fixtures.objects_fixture import *  # noqa: F403
from src.fixtures.setup_hook import *  # noqa: F403
from src.fixtures.user_fixtures import *  # noqa: F403
from src.fixtures.visit_fixtures import *  # noqa: F403
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


def _safe_nodeid(nodeid: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", nodeid)


def _safe_log_filename(nodeid: str, max_stem_len: int = 180) -> str:
    safe_nodeid = _safe_nodeid(nodeid)
    if len(safe_nodeid) <= max_stem_len:
        return safe_nodeid

    digest = hashlib.sha1(safe_nodeid.encode("utf-8")).hexdigest()[:12]
    keep_len = max_stem_len - len(digest) - 2
    return f"{safe_nodeid[:keep_len]}__{digest}"


def _test_log_path(item: pytest.Item) -> Path:  # noqa: F405
    workerid = "master"
    if hasattr(item.config, "workerinput"):
        workerid = str(item.config.workerinput.get("workerid", "master"))

    base_dir = Path("artifacts/logs/tests") / workerid
    base_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{_safe_log_filename(item.nodeid)}__{time.time_ns()}.log"
    return base_dir / filename


def pytest_addoption(parser: pytest.Parser) -> None:  # noqa: F405
    parser.addoption(
        "--seed",
        action="store",
        default=Config.get("default_seed", 100),  # noqa: F405
        help=
        "Seed for random generators. If not set, a new seed is generated per run (and shared across xdist workers).",
    )
    parser.addoption(
        "--api-coverage",
        action="store_true",
        default=False,
        help="Enable API coverage collection",
    )


def pytest_configure(config: pytest.Config) -> None:  # noqa: F405
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


def pytest_collection_finish(session: pytest.Session) -> None:  # noqa: F405
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
    config: pytest.Config,  # noqa: F405
    items: List[pytest.Item],  # noqa: F405
):
    preferred = "chromium"

    filtered: List[pytest.Item] = []  # noqa: F405

    for item in items:
        is_ui = bool(item.get_closest_marker("ui"))
        fixts = getattr(item, "fixturenames", ())

        if (not is_ui) and ("browser_name" in fixts):
            callspec = getattr(item, "callspec", None)
            if callspec is not None and "browser_name" in callspec.params:
                bn = norm_browser_name(callspec.params.get("browser_name"))
                if bn != preferred:
                    continue

        filtered.append(item)

    items[:] = filtered


@pytest.hookimpl(tryfirst=True)  # noqa: F405
def pytest_runtest_setup(item: pytest.Item) -> None:  # noqa: F405
    log_path = _test_log_path(item)

    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    item._test_log_path = log_path
    item._test_log_handler = handler

    logging.getLogger(__name__).info("Started test: %s", item.nodeid)


@pytest.hookimpl(hookwrapper=True)  # noqa: F405
def pytest_runtest_makereport(item: pytest.Item, call):  # noqa: F405
    outcome = yield
    report = outcome.get_result()

    if report.when != "teardown":
        return

    log_path = getattr(item, "_test_log_path", None)
    if log_path is None or not Path(log_path).exists():
        return

    try:
        import allure
        allure.attach.file(str(log_path), name="test.log", attachment_type=allure.attachment_type.TEXT)
    except Exception:
        pass


@pytest.hookimpl(trylast=True)  # noqa: F405
def pytest_runtest_teardown(item: pytest.Item) -> None:  # noqa: F405
    handler = getattr(item, "_test_log_handler", None)
    if handler is None:
        return

    logging.getLogger(__name__).info("Finished test: %s", item.nodeid)

    root_logger = logging.getLogger()
    root_logger.removeHandler(handler)
    handler.close()


@pytest.fixture(scope="session")  # noqa: F405
def browser_name(request):
    return request.config.getoption("--browser")


@pytest.fixture(scope="session")  # noqa: F405
def browser_type_launch_args(browser_type: BrowserType):
    return {
        "headless": Config.get_bool("HEADLESS"),  # noqa: F405
        "slow_mo": 300,  # 👈 необязательно, но очень помогает
    }


@pytest.fixture(scope="session")  # noqa: F405
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport":
            {
                "width": Config.get_int("BROWSER_WIDTH", 1920),  # noqa: F405
                "height":
                    Config.get_int("BROWSER_HEIGHT", 1080)  # noqa: F405
            }
    }


def pytest_sessionfinish(session, exitstatus):
    if not session.config.getoption("--api-coverage"):
        return

    generate_swagger_operations()
    ApiCoverageCollector.save(Path("artifacts/api_coverage/covered_operations.json"))
    calculate_and_save_summary()
