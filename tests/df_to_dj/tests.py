"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
import datetime
import pandas as pd
import numpy as np
import pandas_love_ponies as plp
from models import MyModel
from models import MyModelWithDates


# monkey patch.
pd.DataFrame.to_django = plp.to_django
pd.DataFrame.validate_for_django = plp.validate_for_django



class PLPValidateTest(TestCase):
    def triple_assert_check(self, exception, method, df, *args, **kwargs):
        """
        Check assertion raised against all three calls.

        * calling the ._test_* method raises exception
        * calling the .validate_for_django method raises exception
        * calling the .to_django method raises exception, if validate kwarg.
        """
        self.assertRaises(exception,
                          method,
                          df,
                          *args)
        self.assertRaises(exception,
                          plp.validate_for_django,
                          df,
                          *args)
        self.assertRaises(exception,
                          plp.to_django,
                          df,
                          *args,
                          validate=True)

    def setUp(self):
        self.data = {
            'name1': ['a', 'b', np.nan],
            'name2': ['a', None, np.nan],
            'name3': ['a', 'b', np.nan],
            'b': [3, 2, 1],
            'datetime': [
                datetime.datetime(2013, 1, 1),
                datetime.datetime(2013, 1, 2, 12),
                datetime.datetime(2013, 2, 1),
            ],
            'date': [
                datetime.date(2013, 1, 1),
                datetime.date(2013, 1, 2),
                datetime.date(2013, 2, 1),
            ],
        }

    def test_correct_columns(self):
        df = pd.DataFrame(self.data)
        df['foobar'] = 0
        is_valid = plp.core._test_no_missing_columns(df, MyModel)
        self.assertTrue(is_valid)

        df = pd.DataFrame(self.data)
        df.index.name = 'foobar'
        is_valid = plp.core._test_no_missing_columns(df, MyModel)
        self.assertTrue(is_valid)

        df = pd.DataFrame(self.data)
        self.triple_assert_check(plp.PandasLovesPoniesException,
                                 plp.core._test_no_missing_columns,
                                 df,
                                 MyModel)


    def test_dates_arent_strings(self):
        df = pd.DataFrame(self.data)
        df.index.name = 'foobar'
        is_valid = plp.core._test_dates_arent_strings(df, MyModelWithDates)
        self.assertTrue(is_valid)

        df = pd.DataFrame(self.data)
        df.index.name = 'foobar'
        df['date'] = df['date'].astype(str)
        self.triple_assert_check(plp.PandasLovesPoniesException,
                                 plp.core._test_dates_arent_strings,
                                 df,
                                 MyModelWithDates)

        df = pd.DataFrame(self.data)
        df.index.name = 'foobar'
        df['datetime'] = pd.DatetimeIndex(self.data['datetime'])
        is_valid = plp.core._test_dates_arent_strings(df, MyModelWithDates)
        self.assertTrue(is_valid)


    def test_invalid_nulls(self):
        df = pd.DataFrame(self.data)
        df.index.name = 'foobar'
        self.triple_assert_check(plp.PandasLovesPoniesException,
                                 plp.core._test_invalid_nulls,
                                 df,
                                 MyModelWithDates)

        df = pd.DataFrame(self.data)
        df.index.name = 'foobar'
        df['name1'] = list('abc')
        df['name2'] = list('123')
        # handle numpy NaT
        dates = [
            datetime.datetime(2013, 1, 1),
            np.nan,
            datetime.datetime(2013, 1, 3),
        ]
        df['datetime'] = pd.DatetimeIndex(dates)
        self.triple_assert_check(plp.PandasLovesPoniesException,
                                 plp.core._test_invalid_nulls,
                                 df,
                                 MyModelWithDates)

        df = pd.DataFrame(self.data)
        df.index.name = 'foobar'
        df['name1'] = 'hello'
        df['name2'] = 'world'
        is_valid = plp.core._test_invalid_nulls(df, MyModelWithDates)
        self.assertTrue(is_valid)
        self.assertTrue(df.validate_for_django(MyModelWithDates))

        df = pd.DataFrame(self.data)
        df.index.name = 'foobar'
        # test handling of defaults.
        df['name1'] = ['hello', np.nan, 'hello']
        df['name2'] = 'world'
        is_valid = plp.core._test_invalid_nulls(df, MyModelWithDates)
        self.assertTrue(is_valid)
        self.assertTrue(df.validate_for_django(MyModelWithDates))


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
