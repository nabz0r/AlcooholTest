import hashlib, time
from django.http import JsonResponse
from django.db import transaction
from .models import RateBucket

class BodyLimitMiddleware:
    def __init__(self,get_response): self.get_response=get_response
    def __call__(self,request):
        try: size=int(request.META.get('CONTENT_LENGTH') or 0)
        except ValueError: return JsonResponse({'error':'Invalid content length.'},status=400)
        if size>6*1024*1024: return JsonResponse({'error':'Request exceeds 6 MiB.'},status=413)
        return self.get_response(request)

class RateLimitMiddleware:
    def __init__(self,get_response): self.get_response=get_response
    def __call__(self,request):
        if request.method=='POST' and request.path.startswith('/api/'):
            # Trust only the direct peer. The reverse proxy overwrites this header.
            peer=request.META.get('HTTP_X_REAL_IP',request.META.get('REMOTE_ADDR','unknown'))
            group='auth' if any(x in request.path for x in ['/login','/register','/setup']) else 'write'
            key=hashlib.sha256(f'{peer}:{group}'.encode()).hexdigest()
            window=int(time.time())//300
            with transaction.atomic():
                RateBucket.objects.get_or_create(key=key,defaults={'window':window})
                bucket=RateBucket.objects.select_for_update().get(key=key)
                bucket.count=bucket.count+1 if bucket.window==window else 1
                bucket.window=window; bucket.save()
                if bucket.count>(20 if group=='auth' else 100):
                    response=JsonResponse({'error':'Too many requests. Try again in five minutes.'},status=429)
                    response['Retry-After']='300'; return response
        return self.get_response(request)
