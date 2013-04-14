Support for writing Pandas DataFrame's to Django models.

    ./manage.py test df_to_dj

to see it in action.

relevant code:

    pandas_love_ponies/__init__.py # has .to_django() method code.
    tests/df_to_dj/tests.py # example of how to call .to_django()

Use case.

    import pandas_love_ponies as plp
    # monkey patch.
    pd.DataFrame.to_django = plp.to_django

    df = pd.DataFrame(some_data)
    df.to_django(SomeModel)
    # OR
    plp.to_django(df, SomeModel)

    from myapp.models import Sale
    df = pd.read_csv('sales.csv')
    df.to_django(Sale)
    # OR
    plp.to_django(df, Sale)

LICENSE: BSD.
