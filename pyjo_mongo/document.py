import pymongo
from bson import ObjectId
from pyjo import Model, Field, ModelMetaclass
from six import with_metaclass

from pyjo_mongo.queryset import Queryset


class DocumentMetaClass(ModelMetaclass):

    @classmethod
    def validate_meta(cls, meta):
        valid_keys = [
            'db_connection',
            'collection_name',
            'indexes',
            'index_background',
            'skip_index_validation',
        ]
        if set(meta.keys()) - set(valid_keys):
            raise Exception('Invalid meta attributes: {}'.format(list(set(meta.keys()) - set(valid_keys))))

    def __new__(mcs, name, bases, attrs):
        mcs.validate_meta(attrs['__meta__'])
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
    def key_path_is_valid(cls, key_path):
        fields = cls._fields
        for key in key_path.split('.'):
            if key not in fields:
                return False
            field = fields[key]
            if isinstance(field._type, Model):
                fields = field._type._fields
            else:
                break
        return True

    @classmethod
    def _minus_fields_to_pymongo_couples(cls, fields):
        pymongo_tuples = []
        for field in fields:

            # check if field is already in pymongo format
            if isinstance(field, tuple):
                if not isinstance(field[0], str) or len(field) != 2:
                    raise Exception('invalid field')
                pymongo_tuples.append(field)
                continue

            # assume field is in pyjo format

            if not isinstance(field, str):
                raise Exception('invalid field')

            if field[0] == '-':
                field = field[1:]
                pymongo_tuples.append((field, pymongo.DESCENDING))
            else:
                pymongo_tuples.append((field, pymongo.ASCENDING))

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

            pymongo_tuples = cls._minus_fields_to_pymongo_couples(fields)

            if not cls.__meta__.get('skip_index_validation'):
                for field, _ in pymongo_tuples:
                    if not cls.key_path_is_valid(field):
                        raise Exception('Field "{}" used in index is not declared in the model'.format(field))

            mongo_indexes.append(pymongo.IndexModel(
                pymongo_tuples,
                background=background,
                **kwargs
            ))

        if mongo_indexes:
            return cls._get_collection(create_indexes=False).create_indexes(mongo_indexes)

    @classmethod
    def drop(cls):
        cls._get_collection().drop()
        cls._indexes_created = False

    def save(self):
        _id = self._get_collection().save(self.to_dict())
        self._id = _id
        return self

    def delete(self):
        if not self._id:
            raise Exception('called delete a document without _id')
        self._get_collection().delete_one({'_id': self._id})
        self._id = None
        return self

    def reload(self):
        if not self._id:
            raise Exception('called reload on a document without _id')
        doc = self.__class__._get_collection().find_one({'_id': self._id})
        if not doc:
            raise Exception('trying to reload non-existent document')
        return self.update_from_dict(doc)
