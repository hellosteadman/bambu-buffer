from logging import getLogger
from django.db.models.signals import post_save

def post_save_receiver(sender, instance, **kwargs):
    from bambu_buffer import post, settings

    found = False
    for m in [list(m) for m in settings.AUTOPOST_MODELS]:
        if not any(m):
            continue

        name = m.pop(0)
        app, model = name.lower().split('.')
        if app != type(instance)._meta.app_label or model != instance._meta.model_name:
            continue

        if any(m):
            author_field = m.pop(0)
        else:
            author_field = 'author'

        if any(m):
            conditions = m.pop(0)
        else:
            conditions = {}

        if any(m):
            post_kwargs = m.pop(0)
        else:
            post_kwargs = {}

        field = type(instance)._meta.get_field_by_name(author_field)
        if not any(field) or field[0] is None:
            continue

        found = True

    if not found:
        return

    if any(conditions):
        query = dict(
            [
                (key, callable(value) and value() or value)
                for (key, value) in conditions.items()
            ]
        )

        if not type(instance).objects.filter(
            pk = instance.pk,
            **query
        ).exists():
            return

    post(
        instance,
        getattr(instance, author_field),
        **dict(
            [
                (key, callable(value) and value() or value)
                for (key, value) in post_kwargs.items()
            ]
        )
    )

post_save.connect(post_save_receiver)
