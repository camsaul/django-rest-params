import unittest

from django.conf import settings
from rest_framework.response import Response

from django_rest_params.decorators import params


class _MockUserManager(object):

    """ Mock Manager object for _MockUser """

    _objects = {}
    _next_id = 1

    def create(self, **kwargs):
        """ Create a mocked model """
        u = _MockUser(**kwargs)
        u.id = _MockUserManager._next_id
        u.pk = u.id
        _MockUserManager._next_id += 1
        _MockUserManager._objects[u.id] = u
        return u

    def get(self, **kwargs):
        """ Fake .get() returns first thing in _objects that matches one of the kwarg pairs """
        for k, v in kwargs.items():
            for id, obj in _MockUserManager._objects.items():
                if k == 'id' or k == 'pk':
                    if obj.id == int(v):
                        return obj
                elif getattr(obj, k) == v:
                    return obj
        raise Exception("Invalid argument(s): .get(%s='%s')" % (k, v))

    def only(self, *args):
        """ Just no-op """
        return self


class _MockUser(object):

    """ A mock model to test that our Django model integration works correctly """

    _default_manager = None  # @params looks for this property to determine if the object if a Django model
    objects = _MockUserManager()

    name = None
    email = None

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class ParamDecoratorTest(unittest.TestCase):

    def setUp(self):
        pass

    def do_fake_request(self, request_fn, expected_status_code=200, method='GET', get={}, post={}):
        """ Perform a fake request to a request fn, check that we got the status code we expected """
        class FakeR(object):
            GET = {}
            POST = {}
            META = {
                'REQUEST_METHOD': None
            }
        fake_request = FakeR()
        fake_request.GET = get
        fake_request.DATA = post
        fake_request.META['REQUEST_METHOD'] = method

        # Did we accidentally make one of these a set?
        self.assertTrue(isinstance(fake_request.GET, dict))
        self.assertTrue(isinstance(fake_request.DATA, dict))

        response = request_fn(fake_request)
        if response.status_code != expected_status_code:
            import pprint
            pp = lambda o: pprint.PrettyPrinter(indent=2).pprint(o)
            print "\n============================== ERROR ==============================\n"
            pp(response.data)
            print "\n===================================================================\n"
            self.assertEqual(response.status_code, expected_status_code)

    def test_int(self):
        """ Test that we can require an 'int' param """

        @params(my_int=int)
        def my_request(request, my_int):
            self.assertTrue(isinstance(my_int, int))
            return Response({'status': 'success'})

        # try without int
        self.do_fake_request(my_request, expected_status_code=400)

        # try with int
        self.do_fake_request(my_request, get={'my_int': 100})

        # try with wrong type
        self.do_fake_request(my_request, expected_status_code=400, get={'my_int': "not an int"})

    def test_float(self):
        """ Test that we can require a 'float' param """
        @params(my_float=float)
        def my_request(request, my_float):
            self.assertTrue(isinstance(my_float, float))
            return Response({'status': 'success'})

        # try without float
        self.do_fake_request(my_request, expected_status_code=400)

        # try with float
        self.do_fake_request(my_request, get={'my_float': 100.0})

        # should still accept an int
        self.do_fake_request(my_request, get={'my_float': 100})

        # try with wrong type
        self.do_fake_request(my_request, expected_status_code=400, get={'my_float': "not an float"})

    def test_str(self):
        """ Test that we can require a 'str' param """

        @params(my_str=str)
        def my_request(request, my_str):
            return Response({'status': 'success'})

        # try without str
        self.do_fake_request(my_request, expected_status_code=400)

        # try with str
        self.do_fake_request(my_request, get={'my_str': 'a str'})

        # try with wrong type
        self.do_fake_request(my_request, expected_status_code=400, get={'my_str': 100})

    def test_unicode(self):
        """ Test that a unicode 'str' works correctly """
        @params(my_str=str)
        def my_request(request, my_str):
            return Response({'status': 'success'})

        self.do_fake_request(my_request, method='POST', post={'my_str': unicode('unicode_str')})

    def test_tuple(self):
        """ Test that we can specify a tuple for param """
        @params(color=('red', 'green'))
        def my_request(request, color):
            self.assertTrue(color == 'red' or color == 'green')
            return Response({'status': 'success'})

        # don't specify param
        self.do_fake_request(my_request, expected_status_code=400, get={})

        # ok, specify something not in tuple
        self.do_fake_request(my_request, expected_status_code=400, get={'color': 'orange'})

        # ok, specify something in tuple
        self.do_fake_request(my_request, get={'color': 'red'})

    def test_django_model(self):
        """ Test that we can specify a Django model for a param """
        @params(user=_MockUser)
        def my_request(request, user):
            self.assertTrue(isinstance(user, _MockUser))
            return Response({'status': 'success'})

        # don't specify
        self.do_fake_request(my_request, expected_status_code=400, get={})

        # specify something not and int
        self.do_fake_request(my_request, expected_status_code=400, get={'user': "Not a User ID"})

        # specify valid
        user = _MockUser.objects.create(name='Cam Saul', email='Myfakeemail@toucan.farm')
        self.assertTrue(user.id)
        self.do_fake_request(my_request, get={'user': user.id})

        # should work with str
        self.do_fake_request(my_request, get={'user': str(user.id)})

    def test_lt(self):
        @params(my_int=int, my_int__lt=100)
        def my_request(request, my_int):
            self.assertTrue(my_int < 100)
            return Response({'status': 'success'})

        # invalid
        self.do_fake_request(my_request, expected_status_code=400, get={'my_int': 100})

        # valid
        self.do_fake_request(my_request, get={'my_int': 99})

    def test_lte(self):
        @params(my_int=int, my_int__lte=100)
        def my_request(request, my_int):
            self.assertTrue(my_int <= 100)
            return Response({'status': 'success'})

        # invalid
        self.do_fake_request(my_request, expected_status_code=400, get={'my_int': 101})

        # valid
        self.do_fake_request(my_request, get={'my_int': 100})

    def test_gt(self):
        @params(my_int=int, my_int__gt=10)
        def my_request(request, my_int):
            self.assertTrue(my_int > 10)
            return Response({'status': 'success'})

        # invalid
        self.do_fake_request(my_request, expected_status_code=400, get={'my_int': 10})

        # valid
        self.do_fake_request(my_request, get={'my_int': 11})

    def test_gte(self):
        @params(my_int=int, my_int__gte=10)
        def my_request(request, my_int):
            self.assertTrue(my_int >= 10)
            return Response({'status': 'success'})

        # invalid
        self.do_fake_request(my_request, expected_status_code=400, get={'my_int': 9})

        # valid
        self.do_fake_request(my_request, get={'my_int': 10})

    def test_str_length_gt_lt(self):
        """ Test that lt/gt (etc) work on len(str) """
        @params(my_str=str, my_str__length__lt=5, my_str__length__gte=2)
        def my_request(request, my_str):
            self.assertTrue(len(my_str) < 5)
            self.assertTrue(len(my_str) >= 2)
            return Response({'status': 'success'})

        # invalid
        self.do_fake_request(my_request, expected_status_code=400, get={'my_str': 'THIS STRING IS WAY TOO LONG'})

        # valid
        self.do_fake_request(my_request, get={'my_str': 'GOOD'})

    def test_str_length_eq(self):
        """ Test that str__length__eq works """
        @params(my_str=str, my_str__length__eq=4)
        def my_request(request, my_str):
            self.assertEqual(len(my_str), 4)
            return Response({'status': 'success'})

        # invalid
        self.do_fake_request(my_request, expected_status_code=400, get={'my_str': 'THIS STRING IS WAY TOO LONG'})

        # valid
        self.do_fake_request(my_request, get={'my_str': 'GOOD'})

    def test_optional(self):
        """ Test that we can make a param optional """
        @params(my_int=int, my_int__optional=True)
        def my_request(request, my_int):
            self.assertEqual(my_int, None)
            return Response({'status': 'success'})

        self.do_fake_request(my_request, get={})  # don't set it

    def test_default(self):
        """ Test that we can specify a default value for a param """
        @params(my_int=int, my_int__default=100)
        def my_request(request, my_int):
            self.assertEqual(my_int, 100)
            return Response({'status': 'success'})

        self.do_fake_request(my_request, get={})  # don't set it

    def test_name(self):
        """ Test that we can specify a name for the param different from what we'll call it in our function """
        @params(my_int=int, my_int__name='my_int_param')
        def my_request(request, my_int):
            self.assertEqual(my_int, 100)
            return Response({'status': 'success'})

        self.do_fake_request(my_request, get={'my_int_param': 100})

    def test_deferred(self):
        """ Test that we can make a Django model deferred, or not """
        # TODO

    def test_method_get(self):
        """ Test that we can specify param must be 'GET' """
        @params(my_int=int, my_int__method='GET')
        def my_request(request, my_int):
            self.assertEqual(my_int, 100)
            return Response({'status': 'success'})

        self.do_fake_request(my_request, method='POST', get={'my_int': 100})
        self.do_fake_request(my_request, method='POST', expected_status_code=400, post={'my_int': 100})

    def test_method_post(self):
        """ Test that we can specify param must be 'POST' """
        @params(my_int=int, my_int__method='POST')
        def my_request(request, my_int):
            self.assertEqual(my_int, 100)
            return Response({'status': 'success'})

        self.do_fake_request(my_request, method='POST', expected_status_code=400, get={'my_int': 100})
        self.do_fake_request(my_request, method='POST', post={'my_int': 100})

    def test_method_any(self):
        """ Test that we can allow either GET or POST. """
        @params(my_int=int, my_int__method=('GET', 'POST'))
        def my_request(request, my_int):
            self.assertEqual(my_int, 100)
            return Response({'status': 'success'})

        self.do_fake_request(my_request, method='POST', get={'my_int': 100})
        self.do_fake_request(my_request, method='POST', post={'my_int': 100})

    def test_many(self):
        """ Test that __many=True will let yoy pass CSV or JSON Array params """
        @params(user_ids=int, user_ids__many=True)
        def my_request(request, user_ids):
            self.assertEqual(user_ids[-1], 100)
            return Response({'status': 'success'})

        # single val should work
        self.do_fake_request(my_request, get={'user_ids': 100})

        # multiple vals should work
        self.do_fake_request(my_request, get={'user_ids': '98,99,100'})

        # POST - single val
        self.do_fake_request(my_request, method='POST', post={'user_ids': 100})

        # POST - multiple vals
        self.do_fake_request(my_request, method='POST', post={'user_ids': [87, 97, 100]})

    def test_field(self):
        """ Test that __field works correctly. """
        @params(user=_MockUser, user__field='name', user__deferred=False)
        def my_request(request, user):
            self.assertEqual(user.name, 'Cam Saul')
            return Response({'status': 'success'})

        _MockUser.objects.create(name='Cam Saul', email='rasta@toucan.farm')

        # try wrong name
        self.do_fake_request(my_request, expected_status_code=400, get={'user': 'Cam'})

        # try right name
        self.do_fake_request(my_request, get={'user': 'Cam Saul'})

    def test_field_unicode(self):
        """ Test that we can get a model if the field is Unicode-encoded. E.g. SuperCategory 1's name is 'Café'. """
        @params(user=_MockUser, user__field='name')
        def my_request(request, user):
            self.assertEqual(user.name, u"Café")
            return Response({'status': 'success'})

        u = _MockUser.objects.create(name=u'Café')
        self.assertEqual(u.name, u'Café')

        self.do_fake_request(my_request, get={'user': u'Café'})


if __name__ == '__main__':
    settings.configure()

    unittest.main()
