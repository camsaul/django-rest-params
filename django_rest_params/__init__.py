from functools import wraps

from rest_framework import status
from rest_framework.response import Response


def params(**kwargs):
    """
        Request fn decorator that builds up a list of params and automatically returns a 400 if they are invalid.
        The validated params are passed to the wrapped function as kwargs.
    """
    # Types that we'll all for as 'tuple' params
    TUPLE_TYPES = tuple, set, frozenset, list
    VALID_TYPES = int, float, str

    class ParamValidator(object):
        # name
        param_name = None  # the name of the param in the request, e.g. 'user_id' (even if we pass 'user' to the Fn)

        # type
        param_type = None

        # method - explicitly allow a certain method. If both are false we'll use defaults
        allow_GET = False
        allow_POST = False

        # value validators
        gt = None
        gte = None
        lt = None
        lte = None
        eq = None

        # optional
        optional = False
        default = None

        # multiple vals
        many = False

        # django models only
        deferred = True
        field = 'id'

        def __init__(self, arg_name, **kwargs):
            self.param_name = arg_name
            for k, v in kwargs.items():
                setattr(self, k, v)

        def check_type(self, param):
            """ Check that the type of param is valid, or raise an Exception. This doesn't take self.many into account. """
            valid_type = True
            if isinstance(self.param_type, TUPLE_TYPES):
                if not param in self.param_type:
                    raise Exception('invalid option "%s": Must be one of: %s' % (param, self.param_type))
            else:
                if self.param_type == int:
                    param = int(param)
                elif self.param_type == float:
                    param = float(param)
                elif self.param_type == str:
                    assert(isinstance(param, (str, unicode)))
                    param = unicode(param)
                elif self.param_type == bool:
                    param = bool(param)
                elif hasattr(self.param_type, '_default_manager'):  # isinstance(django.models.Model) doesn't seem to work, but this is a good tell
                    query_set = self.param_type.objects
                    if self.deferred:
                        query_set = query_set.only('id')
                    param = query_set.get(**{self.field: param})
                else:
                    valid_type = False
            if not valid_type:
                raise Exception("Invalid param type: %s" % self.param_type.____name__)
            return param

        def check_value(self, param):
            """ Check that a single value is lt/gt/etc. Doesn't take self.many into account. """
            val = None
            if self.param_type == int or self.param_type == float:
                val = param
            elif self.param_type == str:
                val = len(param)
            if val:
                try:
                    if self.eq and val != self.eq:
                        raise Exception("must be less than %s!" % self.eq)
                    else:
                        if self.lt and val >= self.lt:
                            raise Exception("must be less than %s!" % self.lt)
                        if self.lte and val > self.lte:
                            raise Exception("must be less than or equal to %s!" % self.lte)
                        if self.gt and val <= self.gt:
                            raise Exception("must be greater than %s!" % self.gt)
                        if self.gte and val < self.gte:
                            raise Exception("must be greater than or equal to %s!" % self.gte)
                except Exception as e:
                    msg = str(e)
                    msg = ("Length " if self.param_type == str else 'Value ') + msg
                    raise Exception(msg)

    validators = {}

    for k, v in kwargs.items():
        parts = k.split('__')
        param_key = parts[0]

        if not param_key in validators:
            validators[param_key] = ParamValidator(param_key)
        obj = validators[param_key]

        if (len(parts) == 1):
            # set type
            if not hasattr(v, '_default_manager'):  # django model
                if not isinstance(v, TUPLE_TYPES) and not v in VALID_TYPES:
                    raise Exception("Invalid type for %s: %s is not a valid type" % (k, v))
            obj.param_type = v
        else:
            # we only are interested in the last part, since the only thing that can be multipart is __length__eq (etc) and 'length' is not important
            last_part = parts[-1]

            if last_part == 'method':
                if isinstance(v, TUPLE_TYPES):
                    for method in v:
                        if method == 'GET':
                            obj.allow_GET = True
                        elif method == 'POST':
                            obj.allow_POST = True
                        else:
                            raise Exception('Invalid value for __method: "%s"' % method)
                else:
                    if v == 'GET':
                        obj.allow_GET = True
                    elif v == 'POST':
                        obj.allow_POST = True
                    else:
                        raise Exception('Invalid value for __method: "%s"' % v)
                continue

            if last_part == 'name':
                obj.param_name = v
                continue

            BOOL_PARTS = 'deferred', 'optional', 'many'
            if last_part in BOOL_PARTS:
                assert(isinstance(v, bool))
                setattr(obj, last_part, v)
                continue

            NUM_PARTS = 'gt', 'gte', 'lt', 'lte', 'eq'
            if last_part in NUM_PARTS:
                assert(isinstance(v, int) or isinstance(v, float))
                setattr(obj, last_part, v)
                continue

            if last_part == 'default':
                obj.optional = True
                obj.default = v
                continue

            if last_part == 'field':
                assert(isinstance(last_part, str))
                obj.field = v
                continue

            raise Exception("Invalid option: '__%s' in param '%s'" % (last_part, k))

    def _params(fn):

        @wraps(fn)
        def wrapped_request_fn(first_arg, *args, **kwargs):

            if len(args) == 0:
                request = first_arg  # request function is a top-level function
            else:
                request = args[0]  # request fn is a method, first_arg is 'self'

            request_method = request.META['REQUEST_METHOD']
            default_param_method = 'POST' if request_method == 'POST' or request_method == 'PUT' else 'GET'
            # Validate the params
            for arg_name, validator in validators.items():
                param_name = validator.param_name

                # what methods are allowed?
                use_default_methods = not validator.allow_GET and not validator.allow_POST
                allow_GET = (default_param_method == 'GET') if use_default_methods else validator.allow_GET
                allow_POST = (default_param_method == 'POST') if use_default_methods else validator.allow_POST

                # find the param
                param = None
                if allow_POST:
                    param = request.DATA.get(param_name, None)
                    param_type = 'POST'
                if not param and allow_GET:
                    param = request.GET.get(param_name, None)
                    param_type = 'GET'

                try:
                    # optional/default
                    if not param:
                        if not validator.optional:
                            raise Exception('Param is missing')
                        else:
                            kwargs[arg_name] = validator.default
                            continue

                    # check type, value
                    if validator.many:
                        if param_type == 'GET':
                            params = str(param).split(',')
                        else:
                            params = param if isinstance(param, list) else (param,)
                        params = [validator.check_type(p) for p in params]
                        [validator.check_value(p) for p in params]
                    else:
                        param = validator.check_type(param)
                        validator.check_value(param)

                except Exception as e:
                    return Response({'error': 'Invalid param "%s": %s' % (param_name, str(e))}, status=status.HTTP_400_BAD_REQUEST)

                kwargs[arg_name] = params if validator.many else param

            return fn(first_arg, *args, **kwargs)
        return wrapped_request_fn
    return _params
