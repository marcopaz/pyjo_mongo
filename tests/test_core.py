import pymongo
import pytest
from bson import ObjectId
from pyjo import Field, Model
from six import next

from pyjo_mongo import Document
from .conftest import User, Gender, Address, db_connection, TEST_DB_NAME

__author__ = 'gabriele'


@pytest.fixture()
def users():
    for index in range(5):
        User(
            username='test{}'.format(index),
            first_name='guy',
            last_name='bar',
            age=index + 18,
            gender=Gender.male,
        ).save()

    for index in range(5):
        User(
            username='foo{}'.format(index),
            first_name='girl',
            last_name='bar',
            age=index + 18,
            gender=Gender.female,
        ).save()

    return User.objects.find()


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


def test_model_embedded_index():
    class Embedded(Model):
        value = Field(type=int)

    class ModelWithEmbeddedIndex(Document):
        __meta__ = {
            'db_connection': lambda: db_connection[TEST_DB_NAME],
            'indexes': [
                {
                    'fields': ['embedded.value'],
                },
            ]
        }

        embedded = Field(type=Embedded)

    assert ModelWithEmbeddedIndex.objects.count() == 0

    t_model = ModelWithEmbeddedIndex(embedded=Embedded(value=2))
    t_model.save()

    assert ModelWithEmbeddedIndex.objects.count() == 1


def test_model_with_pymongo_fields():

    class SimpleModel(Document):
        __meta__ = {
            'db_connection': lambda: db_connection[TEST_DB_NAME],
            'indexes': [
                {
                    'fields': [
                        ('foo', pymongo.TEXT),
                    ],

                    'default_language': 'english',
                },
            ]
        }

        foo = Field(type=str)

    assert SimpleModel.objects.count() == 0

    t_model = SimpleModel(foo='bar')
    t_model.save()

    assert SimpleModel.objects.count() == 1


def test_meta_validation():
    with pytest.raises(Exception) as err:
        class ModelWithWrongMeta(Document):
            __meta__ = {
                'db_connection_mispelled': lambda: db_connection[TEST_DB_NAME],
                'indexes': [
                    {
                        'fields': ['embedded.value'],
                    },
                ]
            }

            value = Field(type=int)

    assert str(err.value) == "Invalid meta attributes: ['db_connection_mispelled']"


def test_queryset_chaining(users):
    assert User.objects.count() == 10
    assert User.objects.find({'gender': Gender.male.name}).count() == 5
    assert User.objects.find({'gender': Gender.female.name}).count() == 5


def test_can_iterate_results(users):
    count = 0
    for u in User.objects.find({'gender': Gender.male.name}):
        assert u.gender is Gender.male
        count += 1
    assert count == 5


def test_sorting_ascending(users):
    users = User.objects.find({'gender': Gender.male.name}).order_by('age')
    assert users.count() == 5
    assert [u.age for u in users] == [18, 19, 20, 21, 22]


def test_sorting_descending(users):
    users = User.objects.find({'gender': Gender.male.name}).order_by('-age')
    assert users.count() == 5
    assert [u.age for u in users] == [22, 21, 20, 19, 18]


def test_sorting_multiple(users):
    users = User.objects.find().order_by('gender', '-age')
    assert users.count() == 10
    assert [u.age for u in users] == [22, 21, 20, 19, 18, 22, 21, 20, 19, 18]


def test_slicing(users):
    users = list(User.objects.find().order_by('gender', '-age')[:5])
    assert len(users) == 5
    assert [user.age for user in users] == [22, 21, 20, 19, 18]
    assert User.objects.find().order_by('-age')[0].age == 22


def test_skip_and_limit(users):
    users = User.objects.find().order_by('gender', '-age').skip(1).limit(4)
    assert users.count() == 10
    assert [user.age for user in users] == [21, 20, 19, 18]
    assert User.objects.find().order_by('-age')[0].age == 22


def test_next(users):
    users = User.objects.find({'gender': Gender.male.name}).order_by('-age')
    assert users.count() == 5

    user = next(users)
    assert user.age == 22

    user = next(users)
    assert user.age == 21
