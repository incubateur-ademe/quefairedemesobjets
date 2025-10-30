import pytest
from django.http.request import MultiValueDict, QueryDict
from django.test import RequestFactory


@pytest.fixture
def request_factory():
    return RequestFactory()


def query_dict_from(dictionary):
    query_dict = QueryDict("", mutable=True)
    query_dict.update(MultiValueDict(dictionary))
    return query_dict
