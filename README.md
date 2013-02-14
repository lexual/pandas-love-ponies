Support for writing Pandas DataFrame's to Django models.

    ./manage.py test df_to_dj

to see it in action.

relevant code:
    pp/utils.py # has .to_django() method code.
    pp/df_to_dj/tests.py # example of how to call .to_django()

Use case.
    df = pd.DataFrame(some_data)
    df.to_django(SomeModel)

    from myapp.models import Sale
    df = pd.read_csv('sales.csv')
    df.to_django(Sale)
