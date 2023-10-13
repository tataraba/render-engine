import pathlib
import sys
import time
from http.client import HTTPConnection
from http.server import HTTPServer
from importlib import util
from subprocess import PIPE, Popen

import pytest
import requests
from typer.testing import CliRunner
from xprocess import ProcessStarter

from render_engine import Site, cli
from render_engine.watcher import event

runner = CliRunner()

@pytest.fixture(scope="session")
def initialize_project(tmp_path_factory):
    project_root_file: pathlib.Path = tmp_path_factory.getbasetemp()

    cli.init(
        project_folder=project_root_file,
        skip_static=True,
    )
    yield
    # shutil.rmtree(project_root_file)  # uncomment to clean up tmp files


@pytest.fixture(scope="session")  # add _app to sys.modules
def _app(initialize_project, tmp_path_factory) -> Site:
    spec = util.spec_from_file_location("app", tmp_path_factory.getbasetemp() / "app.py")
    module = util.module_from_spec(spec)
    sys.modules["pytest_app"] = module
    spec.loader.exec_module(module)

    return module.app

@pytest.fixture(scope="session")
def build_temp_site(_app: Site, tmp_path_factory):

    _app.output_path = str(tmp_path_factory.getbasetemp() / "output")
    cli.build(
        "pytest_app:app",
    )
    yield
    # shutil.rmtree(project_root_file)  # uncomment to clean up tmp files

@pytest.fixture(scope="module")
def re_server(tmp_path_factory, build_temp_site):
    output_path = tmp_path_factory.getbasetemp() / "output"
    process = Popen(
        ["python", "-m", "http.server", "8123", "--directory", str(output_path)],
        stdout=PIPE,
        encoding="utf-8",
        universal_newlines=True,
    )
    retries = 5
    while retries > 0:
        conn = HTTPConnection('localhost:8123')
        try:
            conn.request('HEAD', '/')
            response = conn.getresponse()
            if response is not None:
                yield process
                break
        except ConnectionRefusedError:
            time.sleep(1)
            retries -= 1
    if not retries:
        raise RuntimeError("Could not start server")
    else:
        process.terminate()
        process.kill()



@pytest.fixture(scope="session")
def regex_handler(_app) -> event.RegExHandler:

    server_address = ("127.0.0.1", 8123)
    _server = HTTPServer(server_address, event.RegExHandler)
    return event.RegExHandler(
        render_engine_server=_server,
        server_address=server_address,
        app=_app,
        patterns=None,
        ignore_patterns=[r".*output\\*.+$", r"\.\\\..+$"],
    )


@pytest.fixture
def watcher_process(xprocess: ProcessStarter, _app):
    command = [
        "python",
        "-m",
        "render_engine",
        "serve",
        "--build",
        "pytest_app:app",
    ]

    watcher_process = xprocess.ensure(
        "watcher_process", command
    )

    yield watcher_process

    xprocess.get_info("watcher_process").terminate()


def test_project_root_file(tmp_path_factory, build_temp_site):
   d = tmp_path_factory.getbasetemp()
   assert (
        d.joinpath("app.py").read_text().strip()
        == pathlib.Path("tests/create_app_check_file_no_site_vars.txt").read_text().strip()
    )


def test_ping_to_output_directory(tmp_path_factory, re_server):
    response = requests.get("http://127.0.0.1:8123")
    assert response.status_code == 200



# def test_app_contains_output_attribute(_app):
#     assert "output" in _app.output_path

# def test_regex_handler_configuration(_app, regex_handler: event.RegExHandler):
#     assert regex_handler.app == _app


# def test_handler_is_called_with_server(regex_handler: event.RegExHandler):
#     assert regex_handler.render_engine_server.server_address == ("127.0.0.1", 8123)

# def test_watcher_is_running(_app, regex_handler: event.RegExHandler):

#     w = event.Watcher(
#         handler=regex_handler,
#         app=_app,
#     )

#     w.run()  # I believe this needs to be started in another thread?
#     assert w.observer.is_alive()

# def test_file_change_causes_server_to_restart():
#     ...

# def test_output_file_is_different_now():
#     ...


# def test_watcher_with_mock_observer(watcher_process):
#     assert watcher_process.is_alive()

