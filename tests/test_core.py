import pytest
from bson import ObjectId
from pyjo import Field

from pyjo_mongo import Document
from .conftest import User, Gender, Address, db_connection, TEST_DB_NAME

__author__ = 'gabriele'


@pytest.fixture()
def user():
    user = User(
        username='test',
        first_name='foo',
        last_name='bar',
        age=23,
        gender=Gender.male,
        address=Address(
            city='Foobar',
            postal_code=12345,
            address={
                'some_key': 'some_value'
            }
        ),
    )
    user.save()
    return user


def test_user_creation():
    u = User(username='test')
    assert u.id is None
    u.save()
    assert ObjectId().is_valid(u.id)


def test_user_retrieval(user):
    u2 = User.objects.find_one({'username': 'test'})
    assert u2.username == 'test'
    assert u2.first_name == 'foo'
    assert u2.last_name == 'bar'
    assert u2.age == 23
    assert u2.gender == Gender.male
    assert u2.address.city == 'Foobar'
    assert u2.address.postal_code == 12345
    assert u2.address.address['some_key'] == 'some_value'


def test_reload(user):
    assert user.first_name == 'foo'

    u2 = User.objects.find_one({'username': 'test'})
    u2.first_name = 'baz'
    u2.save()

    user.reload()

    assert user.first_name == 'baz'


def test_with_id(user):
    u = User.objects.with_id(user.id)
    assert u.username == 'test'
    assert u.first_name == 'foo'
    assert u.last_name == 'bar'
    assert u.age == 23
    assert u.gender == Gender.male
    assert u.address.city == 'Foobar'
    assert u.address.postal_code == 12345
    assert u.address.address['some_key'] == 'some_value'

    assert u.id == user.id


def test_with_ids(user):
    another = User(username='bar')
    another.save()

    users = User.objects.with_ids([user.id, another.id])

    ids = {u.id for u in users}

    assert ids == {user.id, another.id}


def test_delete(user):
    assert User.objects.count() == 1
    user.delete()
    assert User.objects.count() == 0


def test_no_results():
    user = User.objects.find_one({'username': 'not_exists'})
    assert user is None


def test_model_no_indexes():
    class ModelWithNoIndexes(Document):
        __meta__ = {
            'db_connection': lambda: db_connection[TEST_DB_NAME],
            'indexes': [],
        }

        foo = Field(type=str)

    assert ModelWithNoIndexes.objects.count() == 0

    t_model = ModelWithNoIndexes(foo='bar')
    t_model.save()

    assert ModelWithNoIndexes.objects.count() == 1
