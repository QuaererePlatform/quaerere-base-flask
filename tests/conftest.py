from flask import Flask
import pytest


def create_app():
    app = Flask(__name__)
    return app


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()

    yield client
