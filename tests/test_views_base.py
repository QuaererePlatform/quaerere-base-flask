from unittest import mock

from arango.exceptions import DocumentInsertError
from arango.response import Response
from arango.request import Request
from flask import Flask
from marshmallow import Schema, fields

from quaerere_base_flask.views.base import BaseView

MOCK_DATA = [
    {"_key": "1",
     "mockData_1": "foo",
     "mockData_2": "bar", },
    {"_key": "2",
     "mockData_1": "baz",
     "mockData_2": "qux", },
    {"_key": "3",
     "mockData_1": "spam",
     "mockData_2": "eggs", }, ]


class MockSchema(Schema):
    _key = fields.String()
    mockData_1 = fields.String(required=True)
    mockData_2 = fields.String()


class TestBaseView:

    @classmethod
    def setup_class(cls):
        cls.get_db = mock.MagicMock()
        get_db = cls.get_db

        class MockView(BaseView):
            _get_db = get_db
            _obj_model = mock.MagicMock()
            _obj_schema = MockSchema

        cls.app = Flask(__name__)
        cls.app.config['TESTING'] = True
        MockView.register(cls.app)
        cls.client = cls.app.test_client()

    def setup_method(self):
        self.get_db_ret = self.get_db.return_value

    def teardown_method(self):
        self.get_db.reset_mock(return_value=True, side_effect=True)

    def test_index(self):
        self.get_db_ret.query.return_value.all.return_value = MOCK_DATA
        response = self.client.get('/mock/')
        assert response.status_code == 200
        assert response.get_json() == MOCK_DATA

    def test_get(self):
        self.get_db_ret.query.return_value.by_key.return_value = MOCK_DATA[1]
        mock_key = "2"
        response = self.client.get(f'/mock/{mock_key}/')
        assert response.status_code == 200
        assert response.get_json() == MOCK_DATA[1]

    def test_post(self):
        import json
        mock_data = {
            "mockData_1": "spam",
            "mockData_2": "eggs", }
        db_metadata = {
            "_id": "MockData/4",
            "_key": "4",
            "_rev": "fjhsiz=", }
        self.get_db_ret.add.return_value = db_metadata
        response = self.client.post('/mock/',
                                    data=json.dumps(mock_data),
                                    content_type='application/json')
        assert response.status_code == 201
        assert response.get_json() == db_metadata

    def test_post_empty(self):
        response = self.client.post('/mock/')
        assert response.status_code == 400
        assert response.get_json() == {'errors': 'No data received'}

    def test_post_invalid(self):
        import json
        mock_data = {
            "mockData_1": 1,
            "mockData_2": {"foo": "bar"}, }
        response = self.client.post('/mock/',
                                    data=json.dumps(mock_data),
                                    content_type='application/json')
        assert response.status_code == 400
        assert response.get_json() == {
            "errors": {
                "mockData_1": ["Not a valid string."],
                "mockData_2": ["Not a valid string."], }, }

    def test_post_duplicate(self):
        import json
        mock_data = {
            "mockData_1": "spam",
            "mockData_2": "eggs", }
        resp = mock.MagicMock(Response)
        resp.url = 'http://testing.test'
        resp.error_message = 'Dup'
        resp.status_code = 409
        request = mock.MagicMock(Request)

        self.get_db_ret.add.side_effect = DocumentInsertError(resp, request, )
        response = self.client.post('/mock/',
                                    data=json.dumps(mock_data),
                                    content_type='application/json')
        assert response.status_code == 409
