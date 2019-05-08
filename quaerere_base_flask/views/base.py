__all__ = ['BaseView']

import logging

from arango.exceptions import DocumentInsertError
from flask import jsonify, request
from flask_classful import FlaskView

from quaerere_base_flask.schemas import db_metadata_schema

LOGGER = logging.getLogger(__name__)


class BaseView(FlaskView):
    """Base class for defining a Restful access method to a resource

    BaseView provides basic Restful access to a resource defined by a given
    data object and schema.

    Current supported functionality
     * :py:meth:`index`
     * :py:meth:`get`
     * :py:meth:`post`
    """

    def __init__(self, model, schema, get_db,
                 db_resp_schema=db_metadata_schema):
        """

        :param model: Model class for data encapsulation
        :param schema: Schema class for data validation
        :param get_db: Function reference for acquiring a DB connection
        :param db_resp_schema: Special DB response schema for add
        """
        self._model = model
        self._schema = schema()
        self._schema_many = schema(many=True)
        self._db_resp_schema = db_resp_schema
        self._get_db = get_db

    def index(self):
        """Returns all objects

        :returns: All objects of the model type
        """
        db_conn = self._get_db()
        db_result = db_conn.query(self._model).all()
        return jsonify(self._schema_many.dump(db_result).data)

    def get(self, key):
        """Get a specific object by key

        :param key: Primary key of an object to retrieve
        :returns: Object of provided key
        """
        db_conn = self._get_db()
        db_result = db_conn.query(self._model).by_key(key)
        return jsonify(self._schema.dump(db_result).data)

    def post(self):
        """Create a new object
        """
        db_conn = self._get_db()
        if request.data:
            LOGGER.debug(f'Received POST data', extra={'data': request.data})
        else:
            msg = {'errors': 'No data received'}
            return jsonify(msg), 400
        unmarshal = self._schema.load(request.get_json())
        if len(unmarshal.errors) == 0:
            try:
                result = db_conn.add(unmarshal.data)
                return jsonify(self._db_resp_schema.dump(result).data), 201
            except DocumentInsertError as e:
                return jsonify({'errors': e.error_message}), e.http_code
        else:
            return jsonify({'errors': unmarshal.errors}), 400
