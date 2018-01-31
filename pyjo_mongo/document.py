import pymongo
from bson import ObjectId
from pyjo import Model, Field, ModelMetaclass
from six import with_metaclass

from pyjo_mongo.queryset import Queryset


class DocumentMetaClass(ModelMetaclass):
    def __new__(mcs, name, bases, attrs):
        new_class = super(DocumentMetaClass, mcs).__new__(mcs, name, bases, attrs)
        new_class.objects = Queryset(new_class)
        return new_class


class Document(with_metaclass(DocumentMetaClass, Model)):
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
    def _minus_fields_to_pymongo_couples(cls, *fields):
        pymongo_tuples = []
        for field in fields:
            if not isinstance(field, str):
                raise Exception('invalid field')

            if field[0] == '-':
                field = field[1:]
                pymongo_tuples.append((field, pymongo.DESCENDING))
            else:
                pymongo_tuples.append((field, pymongo.ASCENDING))

            if field not in cls._fields:
                raise Exception('Field "{}" used in index is not declared in the model'.format(field))

        return pymongo_tuples

    @classmethod
    def _create_indexes(cls):
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

            pymongo_tuples = cls._minus_fields_to_pymongo_couples(*fields)

            mongo_indexes.append(pymongo.IndexModel(
                pymongo_tuples,
                background=background,
                **kwargs,
            ))

        if mongo_indexes:
            return cls._get_collection(create_indexes=False).create_indexes(mongo_indexes)

    def save(self):
        _id = self._get_collection().save(self.to_dict())
        self._id = _id
        return self

    def delete(self):
        self._get_collection().delete_one(self.to_dict())
        self._id = None
        return self

    def reload(self):
        if not self._id:
            raise Exception('called reload on a document without _id')
        doc = self.__class__._get_collection().find_one({'_id': self._id})
        if not doc:
            raise Exception('trying to reload non-existent document')
        return self.update_from_dict(doc)
