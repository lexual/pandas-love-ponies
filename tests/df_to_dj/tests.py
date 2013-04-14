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


class SimpleTest(TestCase):
    def test_basics(self):
        """
        This is just a way to demo things are working.
        """
        # TODO: actually write test-cases.
        # TODO: write better example data & model.

        data = {
            'name1': ['a', 'b', np.nan],
            'name2': ['a', None, np.nan],
            'name3': ['a', 'b', np.nan],
            'b': [3, 2, 1]
        }
        df = pd.DataFrame(data)
        df.index.name = 'foobar'

        print 'first call to .to_django()', '-' * 44
        print df.head()
        df.to_django(MyModel)
        print MyModel.objects.all().count()
        for mm in MyModel.objects.all():
            print mm

        print 'second call to .to_django()', '-' * 44
        print df.head()
        df.to_django(MyModel, update=True)

        df = pd.DataFrame(df.groupby(['name1', 'name2']).b.sum())
        df['foobar'] = 3
        MyModel.objects.all().delete()
        print 'third call to .to_django()', '-' * 44
        print df.head()
        df.to_django(MyModel)
        print MyModel.objects.all().count()
        for mm in MyModel.objects.all():
            print mm

        self.assertEqual(1 + 1, 2)
