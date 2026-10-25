import hashlib
from redis.exceptions import RedisError
from functools import wraps
from django.core.cache import cache
from django.db import connection

def public_cache(seconds=60):
    def decorate(fn):
        @wraps(fn)
        def inner(request,*args,**kwargs):
            if connection.in_atomic_block: return fn(request,*args,**kwargs)
            try: revision=cache.get_or_set('catalogue:revision','initial',timeout=None)
            except (RedisError,OSError): return fn(request,*args,**kwargs)
            key='public:'+hashlib.sha256((str(revision)+request.get_full_path()).encode()).hexdigest()
            try: response=cache.get(key)
            except (RedisError,OSError): return fn(request,*args,**kwargs)
            if response is not None:
                response['X-Alcooltest-Cache']='HIT';return response
            response=fn(request,*args,**kwargs)
            if response.status_code==200:
                try: cache.set(key,response,timeout=seconds)
                except (RedisError,OSError): pass
                response['X-Alcooltest-Cache']='MISS'
            return response
        return inner
    return decorate
