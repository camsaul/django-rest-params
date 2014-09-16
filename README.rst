Django REST Params
=======================

Request function decorator that builds up a list of params and automatically returns a 400 if they are invalid.
The validated params are passed to the wrapped function as kwargs.

########
Examples
########

    from django_rest_params.decorators import params
    
    @params(latitude=float, latitude__gte=-90.0, latitude__lte=90.0,
            longitude=float, longitude__gte=-180.0, longitude__lte=180.0)
    def get_something(request, latitude, longitude):
        # ....


TYPE
Specify the type of a param:
  latitude=float
valid options are:
  * int
  * float
  * bool
  * str/unicode
  * tuple/list/set/frozenset (which will be treated as a list of valid options)
  * a django Model subclass (in which case the param will be treated as a PK to that Model)
 GT/LT/GTE/LTE
Automatically check that a param falls within a certain range. Valid for float, int, or Model PK, which all do numerical comparisons.
  latitude__gte=-90.0
  latitude__lte=90.0
 LENGTH__LT/GT/LTE/GTE/EQ
Only valid for str params. Check the length of the str
  description__length__lt=256
  country_code__length__eq=2
 OPTIONAL
  latitude__optional=True # same as latitude__default=None
Default is False; if set to True, this param will be checked for validity (it will still return a 400 if it doesn't pass gte checks, for example),
but will be passed to the wrapped function as None if it wasn't specified.
 DEFAULT
  sort_by=('publisher_guides_count', 'most_recent')
  sort_by__default='publisher_guides_count'
 Implies that this param is optional.
 Specify a default value for this param if it isn't specified.
 NAME
By default, we'll look for a param with the same name as the kwargs, e.g.
  user_id=User # look for user_id param, create a User object and pass to wrapped fn as user_id
But sometimes it makes more sense to call such a param 'user', so you can do:
  user=User, user__name='user_id' # look for user_id, assign to user
 MANY
  users=int # param 'users=1' is ok, 'users=1,2' is not
  users__many=True # param 'users=1,2' will return tuple of (1, 2), 'users=1' will return (1)
Allow User to (optionally) specify params as CSV (GET) or Array (JSON POST)
If many==True, the params will be returned as a tuple regardless of whether or not there was only one param
 DEFERRED
  user__deferred=True
By default, Django model params will create an object like this:
  User.objects.only('id').get(id=user_id) # all fields except for 'id' are deferred
Usually, this is what we want, since we don't need to fetch the object from the DB (this is significantly faster than doing so).
However, you can specify not to add the .only() by setting __deferred to False.
 FIELD
  category = Category # by default, do Category.get(id=category)
  category__field='name' # instead, do Category.get(name=category)
Applies to Django models only. By default, we treat the param as an ID; instead, you can treat it as something else, e.g. 'name'
 METHOD
Valid methods for passing this param. Default is 'POST' for POST/PUT requests and GET for all others
  user__method='GET' # GET only
  user__method=('GET', 'POST') # allow either source

This is the description file for the project.

The file should use UTF-8 encoding and be written using ReStructured Text. It
will be used to generate the project webpage on PyPI, and should be written for
that purpose.

Typical contents for this file would include an overview of the project, basic
usage examples, etc. Generally, including the project changelog in here is not
a good idea, although a simple "What's New" section for the most recent version
may be appropriate.
