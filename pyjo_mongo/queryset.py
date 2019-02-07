from bson import ObjectId

__author__ = 'xelhark'


class Queryset(object):
    def __init__(self, cls, cursor=None):
        self.cls = cls
        self._cursor = cursor

    @property
    def cursor(self):
        return self._cursor or self.cls._get_collection()

    def with_id(self, id):
        id = ObjectId(id) if not isinstance(id, ObjectId) else id
        return self.find_one({'_id': id})

    def with_ids(self, ids):
        if not isinstance(ids, list):
            raise Exception('argument must be a list')
        ids = [ObjectId(id) if not isinstance(id, ObjectId) else id for id in ids]
        return self.find({'_id': {'$in': ids}})

    def find(self, *args, **kwargs):
        if self._cursor is not None:
            raise RuntimeError("Chaining find methods is not supported")
        return Queryset(cls=self.cls, cursor=self.cls._get_collection().find(*args, **kwargs))

    def find_one(self, *args, **kwargs):
        """
        Finds and returns a single instance of the requested document class, matching the criteria provided
        :param args: args sent to Mongo for filtering
        :param kwargs: kwargs sent to Mongo for filtering
        :return: The instance of document class requested or None, if not found
        :rtype: cls
        """
        data = self.cursor.find_one(*args, **kwargs)
        if data:
            return self.cls.from_dict(data)

    def order_by(self, *args):
        return Queryset(cls=self.cls, cursor=self.cursor.sort(self.cls._minus_fields_to_pymongo_couples(args)))

    def count(self):
        return self.cursor.count()

    def skip(self, *args, **kwargs):
        return Queryset(cls=self.cls, cursor=self.cursor.skip(*args, **kwargs))

    def limit(self, *args, **kwargs):
        return Queryset(cls=self.cls, cursor=self.cursor.limit(*args, **kwargs))

    def to_list(self):
        return list(self)

    def __getitem__(self, item):
        if isinstance(item, slice):
            return Queryset(cls=self.cls, cursor=self.cursor.__getitem__(item))
        return self.cls.from_dict(self.cursor[item])

    def __iter__(self):
        for element in self.cursor:
            yield self.cls.from_dict(element)

    def __next__(self):
        return self.cls.from_dict(self.cursor.__next__())
