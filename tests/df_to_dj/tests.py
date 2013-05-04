"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
import pandas as pd
import numpy as np
import pandas_love_ponies as plp
from models import MyModel

# monkey patch.
pd.DataFrame.to_django = plp.to_django


class PLPTest(TestCase):
    def setUp(self):
        self.data = {
            'name1': ['a', 'b', np.nan],
            'name2': ['a', None, np.nan],
            'name3': ['a', 'b', np.nan],
            'b': [3, 2, 1]
        }

    def test_basics(self):
        """
        This is just a way to demo things are working.
        """
        # TODO: actually write test-cases.
        # TODO: write better example data & model.

        df = pd.DataFrame(self.data)
        df.index.name = 'foobar'

        print 'first call to .to_django()', '-' * 44
        print df.head()
        df.to_django(MyModel)
        print MyModel.objects.all().count()
        for mm in MyModel.objects.all():
            print mm

        self.assertEqual(len(df), MyModel.objects.all().count())

        print 'second call to .to_django()', '-' * 44
        print df.head()
        df.to_django(MyModel, update=True)

        self.assertEqual(len(df), MyModel.objects.all().count())

        df = pd.DataFrame(df.groupby(['name1', 'name2']).b.sum())
        df['foobar'] = 3
        MyModel.objects.all().delete()
        print 'third call to .to_django()', '-' * 44
        print df.head()
        df.to_django(MyModel)
        print MyModel.objects.all().count()
        for mm in MyModel.objects.all():
            print mm

    def test_kwarg_write_to_db(self):
        df = pd.DataFrame(self.data)
        df.index.name = 'foobar'

        df.to_django(MyModel, write_to_db=False)
        self.assertEqual(0, MyModel.objects.all().count())

        df.to_django(MyModel, write_to_db=True)
        self.assertEqual(len(df), MyModel.objects.all().count())

        # default arg write_to_db
        MyModel.objects.all().delete()
        df.to_django(MyModel)
        self.assertEqual(len(df), MyModel.objects.all().count())

    def test_kwarg_return_objects(self):
        df = pd.DataFrame(self.data)
        df.index.name = 'foobar'

        # default arg return_objects
        objs = df.to_django(MyModel)
        self.assertIsNone(objs)

        MyModel.objects.all().delete()
        objs = df.to_django(MyModel, return_objects=False)
        self.assertIsNone(objs)

        MyModel.objects.all().delete()
        objs = df.to_django(MyModel, return_objects=True)
        self.assertIsNotNone(objs)
        self.assertIsInstance(objs, list)
        self.assertEqual(len(objs), len(df))
