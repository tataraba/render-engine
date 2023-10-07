import pathlib
from http.server import HTTPServer

import pytest
import requests

from render_engine import Site, cli


@pytest.fixture()
def initialize_app_in_test_dir(basic_app_directory):
    d = basic_app_directory / "re_app"
    cli.init(
        project_folder=d,
    )
    return d


def test_basic_app_exists(initialize_app_in_test_dir):
    assert (initialize_app_in_test_dir / "app.py").exists()