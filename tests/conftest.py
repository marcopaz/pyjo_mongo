from enum import Enum

import pytest
from pymongo import MongoClient
from pyjo import Model, Field, RangeField, EnumField
from pyjo_mongo import Document

db_connection = MongoClient('mongodb://localhost:27017')

TEST_DB_NAME = 'pyjo_mongo_tests'

__author__ = 'xelhark'


@pytest.fixture(autouse=True)
def cleanup():
    db_connection.drop_database(TEST_DB_NAME)


class Gender(Enum):
    female = 0
    male = 1


class Address(Model):
    city = Field(type=str)
    postal_code = Field(type=int)
    address = Field()


class User(Document):
    __meta__ = {
        'db_connection': lambda: db_connection[TEST_DB_NAME],
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
    address = Field(type=Address)
    active = Field(type=bool, default=True)
