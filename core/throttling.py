from rest_framework.throttling import AnonRateThrottle

class IPBasedThrottle(AnonRateThrottle):
    rate = '100/hour'
    scope = 'ip_anon'

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            return None  # Chỉ áp dụng cho anonymous
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request)
        }
