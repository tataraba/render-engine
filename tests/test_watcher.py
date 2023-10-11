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

from render_engine import Page, Site, cli
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
def _app(initialize_project, tmp_path_factory):
    spec = util.spec_from_file_location("app", tmp_path_factory.getbasetemp() / "app.py")
    module = util.module_from_spec(spec)
    sys.modules["pytest_app"] = module
    spec.loader.exec_module(module)

    return module.app

@pytest.fixture(scope="session")
def build_temp_site(_app):

    cli.build(
        "pytest_app:app",
    )

    yield

@pytest.fixture(scope="module")
def re_server(tmp_path_factory, initialize_project):
    output = tmp_path_factory.getbasetemp() / "output"
    process = Popen(
        ["python", "-m", "http.server", "8123", "--directory", str(output)],
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




def test_project_root_file(tmp_path_factory, build_temp_site):
   d = tmp_path_factory.getbasetemp()
   assert (
        d.joinpath("app.py").read_text().strip()
        == pathlib.Path("tests/create_app_check_file_no_site_vars.txt").read_text().strip()
    )


def test_app_contains_output_attribute(tmp_path_factory, build_temp_site):
    bapp = sys.modules["pytest_app"]
    bapp.app.render()  # not working??
    assert bapp.app.output_path == "output"


def test_handler_is_called_with_server():
    ...

def test_file_change_causes_server_to_restart():
    ...

def test_output_file_is_different_now():
    ...