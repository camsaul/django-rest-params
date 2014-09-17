Django REST Params
==================

Request function decorator that builds up a list of params and automatically returns a 400 if they are invalid.
The validated params are passed to the wrapped function as kwargs.

A Few Examples
--------------------

.. code:: python

   from django_rest_params.decorators import params
   
   @params(latitude=float, latitude__gte=-90.0, latitude__lte=90.0,
           longitude=float, longitude__gte=-180.0, longitude__lte=180.0)
   def get_something(request, latitude, longitude):
       """ Handles API calls like:
           .../nearby?latitude=37.78&longitude=-122.4
           .../nearby?latitude=40                     Returns error: missing param 'longitude'
           .../nearby?latitude=47&longitude=500.0     Returns error: longitude must be <= 180.0
       """
       pass
        
   @params(offset=int, offset__default=0)
   def paged_api_call(request, offset):
       """ Handles API calls like:
           .../paged_call                             __default value is used if param is not specified
           .../paged_call?offset=100
       """
       pass
        
   @params(colors=('red','blue','green','yellow'), colors__many=True, 
           colors__optional=True, colors__name='color_filter')
   def get_shirts(request, colors):
       """ Handles API calls like:
           .../shirts?color_filter=red                 __name gives lets you use a different name in Django than the actual API param
           .../shirts?color_filter=yellow,blue         __many allows comma-separted list for GET / single val or array for POST
           .../shirts                                  Params are optional
           .../shirts?color_filter=black               This will return an error stating black is invalid, and listing the valid options
       """
       pass

Options
=======

TYPE
----
Specify the type of a param:

.. code:: python

   latitude=float

valid options are:
  - int
  - float
  - bool
  - str/unicode
  - tuple/list/set/frozenset (which will be treated as a list of valid options)
  - a django Model subclass (in which case the param will be treated as a PK to that Model)
  
GT/LT/GTE/LTE
-------------
Automatically check that a param falls within a certain range. Valid for float, int, or Model PK, which all do numerical comparisons.

.. code:: python

   latitude__gte=-90.0
   latitude__lte=90.0
  
LENGTH__LT/GT/LTE/GTE/EQ
------------------------
Only valid for str params. Check the length of the str

.. code:: python

  description__length__lt=256
  country_code__length__eq=2
  
OPTIONAL
--------

.. code:: python

   latitude__optional=True # same as latitude__default=None
   
Default is False; if set to True, this param will be checked for validity (it will still return a 400 if it doesn't pass gte checks, for example),
but will be passed to the wrapped function as None if it wasn't specified.

DEFAULT
-------

.. code:: python

   sort_by=('publisher_guides_count', 'most_recent')
   sort_by__default='publisher_guides_count'
   
 Implies that this param is optional.
 Specify a default value for this param if it isn't specified.
 
NAME
----
By default, we'll look for a param with the same name as the kwargs, e.g.

.. code:: python

   user_id=User # look for user_id param, create a User object and pass to wrapped fn as user_id
   
But sometimes it makes more sense to call such a param 'user', so you can do:

.. code:: python

   user=User, user__name='user_id' # look for user_id, assign to user
  
MANY
----

.. code:: python
   users=int # param 'users=1' is ok, 'users=1,2' is not
   users__many=True # param 'users=1,2' will return tuple of (1, 2), 'users=1' will return (1)
   
Allow User to (optionally) specify params as CSV (GET) or Array (JSON POST)
If many==True, the params will be returned as a tuple regardless of whether or not there was only one param

DEFERRED
--------
.. code:: python

   user__deferred=True

By default, Django REST Params will create an object like this:

.. code:: python

   User.objects.only('id').get(id=user_id) # all fields except for 'id' are deferred

Usually, this is what we want, since we don't need to fetch the object from the DB (this is significantly faster than doing so).
However, you can specify not to add the .only() by setting __deferred to False.

FIELD
-----

.. code:: python

   category = Category # by default, do Category.get(id=category)
   category__field='name' # instead, do Category.get(name=category)
   
Applies to Django models only. By default, we treat the param as an ID; instead, you can treat it as something else, e.g. 'name'

METHOD
------
Valid methods for passing this param. Default is 'POST' for POST/PUT requests and GET for all others

.. code:: python

  user__method='GET' # GET only
  user__method=('GET', 'POST') # allow either source
