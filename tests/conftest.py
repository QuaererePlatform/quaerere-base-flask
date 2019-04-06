from flask import Flask
import pytest

from quaerere_base_flask.views.base import BaseView


def create_app():
    app = Flask(__name__)
    return app


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()

    yield client


class FakeView(BaseView):
    def __init__(self):
        super().__init__()