__all__ = ['db_metadata_schema']

from marshmallow import fields, Schema


class DBMetadata(Schema):
    _id = fields.String()
    _key = fields.String()
    _rev = fields.String()


db_metadata_schema = DBMetadata()
