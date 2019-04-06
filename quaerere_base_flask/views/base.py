__all__ = ['BaseView']

import logging

from arango.exceptions import DocumentInsertError
from flask import jsonify, request
from flask_classful import FlaskView

from quaerere_base_flask.schemas import db_metadata_schema

LOGGER = logging.getLogger(__name__)


class BaseView(FlaskView):

    def __init__(self, model, schema, db_conn,
                 db_resp_schema=db_metadata_schema):
        self._model = model
        self._schema = schema()
        self._schema_many = schema(many=True)
        self._db_resp_schema = db_resp_schema
        self._db_conn = db_conn

    def index(self):
        db_result = self._db_conn.query(self._model).all()
        return jsonify(self._schema_many.dump(db_result).data)

    def get(self, key):
        db_result = self._db_conn.query(self._model).by_key(key)
        return jsonify(self._schema.dump(db_result).data)

    def post(self):
        if request.data:
            LOGGER.debug(f'Received POST data', extra={'data': request.data})
        unmarshal = self._schema.load(request.get_json())
        if len(unmarshal.errors) == 0:
            try:
                result = self._db_conn.add(unmarshal.data)
                return jsonify(self._db_resp_schema.dump(result).data), 201
            except DocumentInsertError as e:
                return jsonify({'errors': e.error_message}), e.http_code
        else:
            return jsonify({'errors': unmarshal.errors}), 400
