__version__ = "0.1.0"


def to_django(self, model, update=False, force_save=False,
              bulk_create_size=1000):
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

    Note
    ----
    Will also attempt to use names of indexes as well as names of columns in
    the DataFrame.
    """
    from django.db.models import fields
    # don't want to edit the df we were given.
    df = self.copy()
    do_bulk_create = not update and not force_save

    obj = model()
    field_names = []
    # Create list of columns in DataFrame that are also in the Django model.
    # Handle NaN's by setting to null if appropriate, or using the default.
    for field in obj._meta.fields:
        if field.name == 'id':
            continue
        if field.name in df or field.name in df.index.names:
            field_names.append(field.name)
            if field.name in df.index.names:
                try:
                    # multi-index
                    df[field.name] = df.index.get_level_values(field.name)
                except AttributeError:
                    # non-multi-index
                    df[field.name] = df.index.values

            has_default = ((field.default is not None) and
                          (field.default is not fields.NOT_PROVIDED))
            if field.null:
                nulls = df[field.name].isnull()
                df[field.name][nulls] = None
            elif has_default:
                df[field.name].fillna(field.default, inplace=True)
            elif isinstance(field, fields.CharField):
                if all(df[field.name].isnull()):
                    df[field.name] = ''
                else:
                    df[field.name].fillna('', inplace=True)

    objs = []
    # iterate through DataFrame, creating/updating Django model instances.
    for _, row in df.iterrows():
        if not update:
            obj = model()
        else:
            unique_togethers = model._meta.unique_together[0]
            kwargs = {field: row[field] for field in unique_togethers}
            obj, _ = model.objects.get_or_create(**kwargs)
        for field_name in field_names:
            setattr(obj, field_name, row[field_name])
        if do_bulk_create:
            objs.append(obj)
            if len(objs) == bulk_create_size:
                model.objects.bulk_create(objs)
                objs = []
        else:
            obj.save()
    if do_bulk_create:
        model.objects.bulk_create(objs)