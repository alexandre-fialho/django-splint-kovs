import warnings

from typing import Callable, Optional, TypeVar, Any
from django.core.cache import cache

_T = TypeVar('_T')
_NOT_FOUND = object()


class splint_cached_property:
    def __init__(
        self,
        func: Callable[..., _T],
        cache_key: Callable[..., _T] = None,
        cache_expires: Optional[int] = None,
    ):
        """Class to saves properties in cache services.

        For more details on how to configure caching services: 
        - https://docs.djangoproject.com/en/4.0/topics/cache/

        Args:
            func (Callable[..., _T]): Callable should be return any 
                picklable Python object.
            cache_key (Callable[..., _T], optional): Callable should be return a sha str. 
                Defaults call to '{func.__name__}__cache_key'.
            cache_expires (Optional[int], optional): The timeout argument is 
                optional and defaults to the timeout argument of the appropriate 
                backend in the CACHES setting. 
                Its the number of seconds the value should be stored in the cache. 
                A timeout of 0 wont cache the value. 
                Defaults to None for timeout will cache the value forever.

        Raises:
            TypeError: Cannot assign the same splint_cached_property to two different names.
            TypeError: Cannot use splint_cached_property instance without calling __set_name__ on it.
            TypeError: No '__dict__' attribute on instance
            TypeError: No '{func.__name__}__cache_key' attribute on instance to cache'

        Returns:
            Picklable: picklable Python object.
        """
        self.func = func
        self.cache_key = cache_key
        self.attrname = None
        self.cache_expires = cache_expires
        self.__doc__ = getattr(func, '__doc__')

    def __set_name__(self, owner, name):
        if self.attrname is None:
            self.attrname = self.func.__name__
        elif name != self.attrname:
            raise TypeError(
                "Cannot assign the same splint_cached_property to two different names "
                f"({self.attrname!r} and {name!r})."
            )

    def __get__(self, instance, cls=None) -> Any:
        if instance is None:
            return self
        if self.attrname is None:
            raise TypeError(
                "Cannot use splint_cached_property instance without calling __set_name__ on it.")

        try:
            instance_cache = instance.__dict__
        # not all objects have __dict__ (e.g. class defines slots)
        except AttributeError:
            msg = (
                f"No '__dict__' attribute on {type(instance).__name__!r} "
                f"instance to cache {self.attrname!r} property."
            )
            raise TypeError(msg) from None

        cache_value = instance_cache.get(self.attrname, _NOT_FOUND)

        if cache_value is _NOT_FOUND:
            if self.cache_key is None:
                try:
                    cache_key = getattr(
                        instance, f'{self.attrname}__cache_key')()
                except AttributeError:
                    msg = (
                        f"No '{self.attrname}__cache_key' attribute on instance to cache "
                        f"{self.attrname!r} property."
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
                instance_cache[self.attrname] = cache_value
            except TypeError:
                msg = (
                    f"The '__dict__' attribute on {type(instance).__name__!r} instance "
                    f"does not support item assignment for caching {self.attrname!r} property."
                )
                warnings.warn(msg, Warning)

        return cache_value
