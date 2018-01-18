import pymongo
from bson import ObjectId
from pyjo import Model, Field


class Document(Model):
    __meta__ = {}
    _indexes_created = False

    _id = Field(type=ObjectId, repr=True)

    @property
    def id(self):
        return self._id

    @classmethod
    def _collection_name(cls):
        return cls.__meta__.get('collection_name') or cls.__name__.lower()

    @classmethod
    def _db_connection(cls):
        client = cls.__meta__.get('db_connection')()
        if client is None:
            raise Exception('no db_connection specified')
        return client

    @classmethod
    def _get_collection(cls, create_indexes=True):
        if create_indexes and not cls._indexes_created:
            cls._create_indexes()
            cls._indexes_created = True
        return cls._db_connection()[cls._collection_name()]

    @classmethod
    def _create_indexes(cls, check_if_fields_exist=True):
        indexes = cls.__meta__.get('indexes', [])
        all_background = cls.__meta__.get('index_background', False)

        mongo_indexes = []

        for index in indexes:
            kwargs = {}
            background = all_background

            if isinstance(index, dict):
                fields = index['fields']
                background = all_background or index.get('index_background') or index.get('background')
                kwargs = {k: v for k, v in index.items() if k not in ['fields', 'index_background', 'background']}
            elif isinstance(index, list) or isinstance(index, tuple):
                fields = index
            else:
                raise Exception('invalid index')

            mongo_fields = []
            for field in fields:
                if not isinstance(field, str):
                    raise Exception('invalid index field')
                if field[0] == '-':
                    field = field[1:]
                    mongo_fields.append((field, pymongo.DESCENDING))
                else:
                    mongo_fields.append((field, pymongo.ASCENDING))

                if check_if_fields_exist and field not in cls._fields:
                    raise Exception('Field "{}" used in index is not declared in the model'.format(field))

            mongo_indexes.append(pymongo.IndexModel(
                mongo_fields,
                background=background,
                **kwargs,
            ))

        return cls._get_collection(create_indexes=False).create_indexes(mongo_indexes)

    def save(self):
        _id = self._get_collection().save(self.to_dict())
        self._id = _id
        return self

    def reload(self):
        if not self._id:
            raise Exception('called reload on a document without _id')
        doc = self.__class__._get_collection().find_one({'_id': self._id})
        if not doc:
            raise Exception('trying to reload non-existent document')
        return self.update_from_dict(doc)

    @classmethod
    def with_id(cls, id):
        id = ObjectId(id) if not isinstance(id, ObjectId) else id
        return cls.find_one({'_id': id})

    @classmethod
    def with_ids(cls, ids):
        if not isinstance(ids, list):
            raise Exception('argument must be a list')
        ids = [ObjectId(id) if not isinstance(id, ObjectId) else id for id in ids]
        return cls.find({'_id': {'$in': ids}})

    @classmethod
    def find(cls, *args, **kwargs):
        docs = cls._get_collection().find(*args, **kwargs)
        for doc in docs:
            yield cls.from_dict(doc)

    @classmethod
    def find_one(cls, *args, **kwargs):
        doc = cls._get_collection().find_one(*args, **kwargs)
        if not doc:
            return doc
        return cls.from_dict(doc)
