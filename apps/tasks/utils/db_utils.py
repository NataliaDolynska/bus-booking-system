from typing import Type

from django.db.models import Model


def if_exists[T: Model](t: Type[T], **kwargs) -> T | bool:
    if t.objects.filter(**kwargs).exists():
        try:
            return t.objects.get(**kwargs)
        except t.DoesNotExist:
            return False
    else:
        return False
