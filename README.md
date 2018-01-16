[![Build Status](https://travis-ci.org/marcopaz/pyjo_mongo.svg?branch=master)](https://travis-ci.org/marcopaz/pyjo_mongo)

# pyjo_mongo

A light wrapper around pymongo and pyjo to easily interact with MongoDB documents. See the following example.

## Install

```
pip install pyjo_mongo
```

## How to use

```python
from pymongo import MongoClient
from pyjo import Model, Field, RangeField, EnumField
from pyjo_mongo import Document

db_connection = MongoClient(MONGODB_URL)[DB_NAME]


class Gender(Enum):
    female = 0
    male = 1


class Address(Model):
    city = Field(type=str)
    postal_code = Field(type=int)
    address = Field()


class User(Document):
    __meta__ = {
        'db_connection': lambda: db_connection,
        'collection_name': 'users',
        'indexes': [
            {
                'fields': ['username'],
                'unique': True,
                'index_background': True,
            },
            ['first_name', 'last_name'],
        ],
    }

    username = Field(type=str, repr=True, required=True)
    first_name = Field(type=str)
    last_name = Field(type=str)
    age = RangeField(min=18, max=120)
    gender = EnumField(enum=Gender)
    address = Field(type=Address, allow_none=True)
    active = Field(type=bool, default=True)
```

```python
u = User(username='mp')
u.id
# None
u.save()
u.id
# ObjectId('5a5ca86080a9b8291874f4db')

u2 = User.find_one({'username': 'mp'})
u2.gender = Gender.male
u2.save()

u.reload()
u.gender
# Gender.male

# queries use the same syntax of pymongo and automatically return pyjo data models
for user in User.find({'active': True}):
    print(user)
# <User(username=mp)>
```

