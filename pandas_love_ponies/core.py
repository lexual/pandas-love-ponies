import pandas as pd
import pytz


class PandasLovesPoniesException(Exception):
    pass


def _has_default(field):
    """
    Does the field have the default attribute set.
    """
    from django.db.models import fields
    has_default = ((field.default is not None) and
                  (field.default is not fields.NOT_PROVIDED))
    return has_default

def _column_getter(df, col):
    """
    Handles getting columns, whether they be true columns, or in index.
    """
    if col in df:
        return df[col]
    elif col in df.index.names:
        try:
            # multi-index
            values = df.index.get_level_values(col)
        except AttributeError:
            # non-multi-index
            values = df.index.values
        return pd.Series(values)


def validate_for_django(self, model):
    """
    Validate the dataframe is valid to be written to the Django model.
    """
    if len(self) == 0:
        return True
    _test_no_missing_columns(self, model)
    _test_dates_arent_strings(self, model)
    _test_invalid_nulls(self, model)
    return True


def _test_no_missing_columns(self, model):
    """
    Are there any necessary columns, that don't exist in the dataframe?
    """
    obj = model()
    for field in obj._meta.fields:
        if field.name == 'id':
            continue
        if _has_default(field):
            continue
        if field.name not in self and field.name not in self.index.names:
            raise PandasLovesPoniesException('missing column: %s' % field.name)
    return True


def _test_dates_arent_strings(self, model):
    from django.db.models import fields
    def is_date_based_field(f):
        if isinstance(f, fields.DateTimeField):
            return True
        elif isinstance(f, fields.DateField):
            return True
        else:
            return False
    obj = model()
    date_fields = [x.name for x in obj._meta.fields
                   if is_date_based_field(x) and x.name != 'id']
    for date_field in date_fields:
        date_series = _column_getter(self, date_field)
        date_value = date_series.values[0]
        if isinstance(date_value, str):
            error_msg = 'date column %s is strings' % date_field
            raise PandasLovesPoniesException(error_msg)
        continue
    return True


def _test_invalid_nulls(self, model):
    """
    If series contains nulls, but django field doesn't allow it.

    Allows if default attribute set, as these will be filled in.
    """
    from django.db.models import fields
    obj = model()
    nonnull_fields = [x for x in obj._meta.fields
                    if not x.null and x.name != 'id']
    for field in nonnull_fields:
        if _has_default(field):
            continue
        nonnull_cols_series = _column_getter(self, field.name)
        if nonnull_cols_series.isnull().any():
            error_msg = '%s column contains nulls' % field.name
            raise PandasLovesPoniesException(error_msg)
    return True


def to_django(self, model, update=False, force_save=False,
              bulk_create_size=1000, utc_to_tz=None, write_to_db=True,
              return_objects=False, validate=False):
    """
    Write DataFrame to SQL database via Django model.

    Parameters
    ----------
    model : Django model
        Model used for writing out the DataFrame's contents.
    update: boolean, default False
        Whether to update existing records, rather than trying to create all
        new ones. It looks up existing records based on the Django model's
        Meta.unique_togethers setting.
    force_save: boolean, default False
        Don't do bulk create of records, force call to model's save() method.
        Use when you have written custom save() method you wish to call.
    bulk_create_size: int, default 1000
        if 'update' is False (default), then will attempt to do a bulk_create
        which is much faster than continually calling Django model's save()
        method.
    utc_to_tz: str, default None
        if set, will conver datetimes from utc to this timezone.
    write_to_db: boolean, default True
        Whether to actually write to the database or not.
    return_objects: boolean, default False
        When True, will return a list of the django objects created from the
        dataframe.
        Defaults to False so that we don't eat memory when dataframe is large.
    validate: boolean, default False
        When true, run validate_for_django() beforehand.


    Note
    ----
    Will also attempt to use names of indexes as well as names of columns in
    the DataFrame.
    """
    from django.db.models import fields
    if validate:
        validate_for_django(self, model)
    # don't want to edit the df we were given.
    df = self.copy()
    do_bulk_create = not update and not force_save
    if utc_to_tz:
        def localize_datetime(x):
            if pd.isnull(x) or isinstance(x, pd.tslib.NaTType):
                return None
            utz_tz = pytz.timezone('UTC')
            local_tz = pytz.timezone(utc_to_tz)
            d = utz_tz.localize(x)
            d = d.astimezone(local_tz)
            # make naive.
            return d.replace(tzinfo=None)

    obj = model()
    relevant_fields = []
    # Create list of columns in DataFrame that are also in the Django model.
    # Handle NaN's by setting to null if appropriate, or using the default.
    for field in obj._meta.fields:
        if field.name == 'id':
            continue
        if field.name in df or field.name in df.index.names:
            relevant_fields.append(field)
            if field.name in df.index.names:
                try:
                    # multi-index
                    df[field.name] = df.index.get_level_values(field.name)
                except AttributeError:
                    # non-multi-index
                    df[field.name] = df.index.values
            if utc_to_tz and isinstance(field, fields.DateTimeField):
                df[field.name] = df[field.name].map(localize_datetime)

            if field.null:
                pass
            elif _has_default(field):
                df[field.name].fillna(field.default, inplace=True)
            elif isinstance(field, fields.CharField):
                if all(df[field.name].isnull()):
                    df[field.name] = ''
                else:
                    df[field.name].fillna('', inplace=True)

    objs = []
    if return_objects:
        all_objs = []
    # iterate through DataFrame, creating/updating Django model instances.
    for _, row in df.iterrows():
        if not update:
            obj = model()
        else:
            try:
                unique_togethers = model._meta.unique_together[0]
                kwargs = {field: row[field] for field in unique_togethers}
            except IndexError:
                for field in model._meta.fields:
                    if field.primary_key:
                        kwargs = {field.name: row[field.name]}
            try:
                obj = model.objects.get(**kwargs)
            except model.DoesNotExist:
                obj = model()

        for field in relevant_fields:
            if field.null and pd.isnull(row[field.name]):
                setattr(obj, field.name, None)
            else:
                setattr(obj, field.name, row[field.name])
        if do_bulk_create:
            objs.append(obj)
            if len(objs) == bulk_create_size:
                if write_to_db:
                    model.objects.bulk_create(objs)
                objs = []
        elif write_to_db:
            obj.save()
        if return_objects:
            all_objs.append(obj)
    if do_bulk_create and write_to_db:
        model.objects.bulk_create(objs)

    if return_objects:
        return all_objs
    else:
        return None
