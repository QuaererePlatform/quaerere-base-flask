__all__ = ['BaseView']

import logging

from arango.exceptions import (
    ArangoServerError,
    AQLQueryExecuteError,
    DocumentInsertError)
from arango_orm.exceptions import DocumentNotFoundError
from flask import jsonify, request
from flask_classful import FlaskView

from quaerere_base_flask.schemas import (
    ArangoDBFilterSchema,
    ArangoDBMetadataSchema)

LOGGER = logging.getLogger(__name__)


class BaseView(FlaskView):
    """Base class for defining a Restful access method to a resource

    BaseView provides basic Restful access to a resource defined by a given
    data object and schema.

    Current supported functionality
     * :py:meth:`index`
     * :py:meth:`get`
     * :py:meth:`post`
     * :py:meth:`put`
     * :py:meth:`patch`
     * :py:meth:`delete`
     * :py:meth:`find`

    Supported callbacks
     * pre and post create (HTTP POST)
     * pre and post read (HTTP GET)
     * pre and post update (HTTP PUT and PATCH)
     * pre and post delete (HTTP DELETE)
    """

    # Function reference for acquiring a DB connection
    _get_db = None
    # Model class for data encapsulation
    _obj_model = None
    # Schema class for data validation
    _obj_schema = None

    def __init__(self):
        """
        """
        if self._get_db is None:
            raise ValueError('_get_db must not be None')
        if self._obj_model is None:
            raise ValueError('_obj_model must not be None')
        if self._obj_schema is None:
            raise ValueError('_obj_schema must not be None')

    # Callbacks for CREATE
    def _pre_create_callback(self, req_data):
        """Call back function ran *before* object is created in data store

        :param req_data: Request data
        :return:
        """
        pass

    def _post_create_callback(self, resp_data):
        """Call back function ran *after* object is created in data store

        :param resp_data: Response data
        :return:
        """
        pass

    # Callbacks for READ
    def _pre_read_callback(self, key):
        """Call back function ran *before* object is read from data store

        :param key: Object key
        :return:
        """
        pass

    def _post_read_callback(self, key, resp_data):
        """Call back function ran *after* object is read from data store

        :param key: Object key
        :param resp_data: Response data
        :return:
        """
        pass

    # Callbacks for UPDATE
    def _pre_update_callback(self, key, req_data, http_method):
        """Call back function ran *before* object is updated in data store

        :param key: Object key
        :param req_data: Request data
        :param http_method: 'patch' or 'put'
        :return:
        """
        pass

    def _post_update_callback(self, key, resp_data, http_method):
        """Call back function ran *after* object is updated in data store

        :param key: Object key
        :param resp_data: Response data
        :param http_method: 'patch' or 'put'
        :return:
        """
        pass

    # Callbacks for DELETE
    def _pre_delete_callback(self, key):
        """Call back function ran *before* object is deleted in data store

        :param key: Object key
        :return:
        """
        pass

    def _post_delete_callback(self, key, resp_data):
        """Call back function ran *before* object is deleted in data store

        :param key: Object key
        :param resp_data: Response data
        :return:
        """
        pass

    def index(self):
        """Returns all objects

        :returns: All objects of the model type
        """
        db_conn = self._get_db()
        db_result = db_conn.query(self._obj_model).all()
        resp_schema = self._obj_schema(many=True)
        return jsonify(resp_schema.dump(db_result).data)

    def get(self, key):
        """Get a specific object by key

        :param key: Primary key of an object to retrieve
        :returns: Object of provided key
        """
        self._pre_read_callback(key)
        db_conn = self._get_db()
        try:
            db_result = db_conn.query(self._obj_model).by_key(key)
        except DocumentNotFoundError:
            return jsonify({'errors': 'Document not found'}), 404
        resp_schema = self._obj_schema()
        resp = resp_schema.dump(db_result).data
        self._post_read_callback(key, resp)
        return jsonify(resp)

    def post(self):
        """Create a new object

        :returns: DB Insert metadata
        """
        db_conn = self._get_db()
        if request.data:
            LOGGER.debug(f'Received POST data', extra={'data': request.data})
        else:
            msg = {'errors': 'No data received'}
            return jsonify(msg), 400
        req_schema = self._obj_schema()
        resp_schema = ArangoDBMetadataSchema()
        req = req_schema.load(request.get_json())
        if len(req.errors) != 0:
            return jsonify({'errors': req.errors}), 400
        self._pre_create_callback(req.data)
        try:
            result = db_conn.add(req.data)
            resp = resp_schema.dump(result).data
            self._post_create_callback(resp)
            return jsonify(resp), 201
        except DocumentInsertError as e:
            return jsonify({'errors': e.error_message}), e.http_code

    def put(self, key):
        """Update all fields on an object

        :param key: Key of object
        :returns: DB Update metadata
        """
        db_conn = self._get_db()
        if request.data:
            LOGGER.debug(f'Received POST data', extra={'data': request.data})
        else:
            msg = {'errors': 'No data received'}
            return jsonify(msg), 400
        data = request.get_json()
        if '_key' not in data:
            data['_key'] = key
        req_schema = self._obj_schema()
        resp_schema = ArangoDBMetadataSchema()
        req = req_schema.load(data)
        if len(req.errors) != 0:
            return jsonify({'errors': req.errors}), 400
        self._pre_update_callback(key, req, 'put')
        try:
            result = db_conn.update(req.data)
            resp = resp_schema.dump(result).data
            self._post_update_callback(key, resp, 'put')
            return jsonify(resp), 201
        except ArangoServerError as e:
            return jsonify({'errors': e.error_message}), e.http_code

    def patch(self, key):
        """Update specific data elements

        :param key: Key of object
        :return: DB Update metadata
        """
        db_conn = self._get_db()
        if request.data:
            LOGGER.debug(f'Received POST data', extra={'data': request.data})
        else:
            msg = {'errors': 'No data received'}
            return jsonify(msg), 400
        data = request.get_json()
        if '_key' not in data:
            data['_key'] = key
        elements = data.keys()
        req_schema = self._obj_schema(only=elements)
        resp_schema = ArangoDBMetadataSchema()
        req = req_schema.load(data)
        if len(req.errors) != 0:
            return jsonify({'errors': req.errors}), 400
        self._pre_update_callback(key, req, 'patch')
        try:
            result = db_conn.update(req.data)
            resp = resp_schema.dump(result).data
            self._post_update_callback(key, resp, 'patch')
            return jsonify(resp), 201
        except ArangoServerError as e:
            return jsonify({'errors': e.error_message}), e.http_code

    def delete(self, key):
        """Delete an object

        :param key: Key of object
        :return: DB Delete metadata
        """
        db_conn = self._get_db()
        resp_schema = ArangoDBMetadataSchema()
        self._pre_delete_callback(key)
        try:
            ent = db_conn.query(self._obj_model).by_key(key)
            result = db_conn.delete(ent)
            resp = resp_schema.dump(result).data
            self._post_delete_callback(key, resp)
            return jsonify(resp), 202
        except ArangoServerError as e:
            return jsonify({'errors': e.error_message}), e.http_code

    def find(self):
        """Find an object based on criteria

        :return: objects
        """
        LOGGER.debug(request.args)
        req_schema = ArangoDBFilterSchema()
        req_args = req_schema.load(request.args)
        if len(req_args.errors) != 0:
            return jsonify({'errors': req_args.errors}), 400
        find_query = req_args.data
        db_conn = self._get_db()
        sort = None
        limit = None
        if 'sort' in find_query:
            sort = find_query['sort']
        if 'limit' in find_query:
            limit = find_query['limit']
        variables = find_query['variables']
        _or = find_query['_or']
        try:
            result = db_conn.query(self._obj_model)
            for condition in find_query['conditions']:
                result = result.filter(condition, _or=_or, **variables)
            if sort is not None:
                result = result.sort(sort)
            if limit is not None:
                result = result.limit(limit)
            obj_schema = self._obj_schema(many=True)
            msg = {'query': find_query,
                   'result': obj_schema.dump(result.all()).data}
        except AQLQueryExecuteError as e:
            return jsonify(
                {'query': find_query,
                 'errors': e.error_message}), e.http_code
        return jsonify(msg), 200
