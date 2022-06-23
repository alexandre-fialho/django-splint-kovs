import json
import warnings

from django.utils.version import PY36, get_docs_version
from typing import Callable, Optional, TypeVar, Any
from django.core.cache import cache

_T = TypeVar('_T')
_NOT_FOUND = object()


class splint_cached_property:
    name = None

    @staticmethod
    def func(instance):
        raise TypeError(
            'Cannot use cached_property instance without calling '
            '__set_name__() on it.'
        )

    @staticmethod
    def _is_mangled(name):
        return name.startswith('__') and not name.endswith('__')

    def __init__(
        self,
        func: Callable[..., _T],
        name: str = None,
        cache_key: Callable[..., _T] = None,
        cache_expires: Optional[int] = 60 * 60 * 3,
    ):
        """Class to saves properties in cache services.

        For more details on how to configure caching services: 
        - https://docs.djangoproject.com/en/4.0/topics/cache/

        Args:
            func (Callable[..., _T]): Callable should be return any 
                picklable Python object.
            name: (Optional[str], , optional): The name of attribute optional,
                by default it will be '{func.__name__}'.
            cache_key (Callable[..., _T], optional): Callable should be return a sha str. 
                Defaults call to '{func.__name__}__cache_key'.
            cache_expires (Optional[int], optional): The timeout argument is 
                optional.
                Its the number of seconds the value should be stored in the cache. 
                A timeout of 0 wont cache the value. 
                Defaults to three hours for expires cache value.

        Raises:
            TypeError: Cannot assign the same splint_cached_property to two different names.
            TypeError: Cannot use splint_cached_property instance without calling __set_name__ on it.
            TypeError: No '__dict__' attribute on instance
            TypeError: No '{func.__name__}__cache_key' attribute on instance to cache'

        Returns:
            Picklable: picklable Python object.
        """

        if PY36:
            self.real_func = func
        else:
            name = name or func.__name__
            if not (isinstance(name, str) and name.isidentifier()):
                raise ValueError(
                    "%r can't be used as the name of a cached property." % name,
                )

            if self._is_mangled(name):
                raise ValueError(
                    'cached property does not work with mangled methods on '
                    'Python < 3.6 without the appropriate `name` argument. See '
                    'https://docs.djangoproject.com/en/%s/ref/utils/'
                    '#cached-property-mangled-name' % get_docs_version(),
                )

            self.name = name
            self.func = func

        self.cache_key = cache_key
        self.cache_expires = cache_expires
        self.__doc__ = getattr(func, '__doc__')

    def __set_name__(self, owner, name):
        if self.name is None:
            self.name = name
            self.func = self.real_func
        elif name != self.name:
            raise TypeError(
                "Cannot assign the same splint_cached_property to two different names "
                f"({self.name!r} and {name!r})."
            )

    def __get__(self, instance, cls=None) -> Any:
        if instance is None:
            return self

        if self.name is None:
            raise TypeError(
                "Cannot use splint_cached_property " +
                "instance without calling __set_name__ on it.")

        try:
            instance_cache = instance.__dict__
        # not all objects have __dict__ (e.g. class defines slots)
        except AttributeError:
            msg = (
                f"No '__dict__' attribute on {type(instance).__name__!r} "
                f"instance to cache {self.name!r} property."
            )
            raise TypeError(msg) from None

        cache_value = instance_cache.get(self.name, _NOT_FOUND)

        if cache_value is _NOT_FOUND:
            if self.cache_key is None:
                try:
                    cache_key = getattr(
                        instance, f'{self.name}__cache_key')()
                except AttributeError:
                    msg = (
                        f"No '{self.name}__cache_key' attribute on instance to cache "
                        f"{self.name!r} property."
                    )
                    raise TypeError(msg) from None
            else:
                cache_key = self.cache_key(instance)

            cache_value = cache.get(cache_key)

        if not cache_value:
            cache_value = self.func(instance)
            cache.set(
                key=cache_key,
                value=cache_value,
                timeout=self.cache_expires)

            try:
                instance_cache[self.name] = cache_value
            except TypeError:
                msg = (
                    f"The '__dict__' attribute on {type(instance).__name__!r} instance "
                    f"does not support item assignment for caching {self.name!r} property."
                )
                warnings.warn(msg, Warning)

        if not isinstance(cache_value, dict):
            try:
                cache_value = json.loads(cache_value)
            except:
                pass

        return cache_value
