__all__ = ['db_metadata_schema']

from marshmallow import fields, Schema


class ArangoDBMetadata(Schema):
    """Schema for ArangoDB insert metadata

    """
    _id = fields.String()
    _key = fields.String()
    _rev = fields.String()


db_metadata_schema = ArangoDBMetadata()
