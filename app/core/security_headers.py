"""
Middleware pour ajouter les headers de sécurité nécessaires
"""

class SecurityHeadersMiddleware:
    """Middleware pour ajouter les headers de sécurité recommandés"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                
                # Headers de sécurité essentiels
                headers[b"x-content-type-options"] = b"nosniff"
                headers[b"x-frame-options"] = b"DENY"
                headers[b"x-xss-protection"] = b"1; mode=block"
                headers[b"referrer-policy"] = b"strict-origin-when-cross-origin"
                
                # Content Security Policy basique
                headers[b"content-security-policy"] = (
                    b"default-src 'self'; "
                    b"script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                    b"style-src 'self' 'unsafe-inline'; "
                    b"img-src 'self' data: https:; "
                    b"font-src 'self' data:; "
                    b"connect-src 'self' ws: wss:; "
                    b"frame-ancestors 'none';"
                )
                
                # Permissions Policy
                headers[b"permissions-policy"] = (
                    b"accelerometer=(), "
                    b"camera=(), "
                    b"geolocation=(), "
                    b"gyroscope=(), "
                    b"magnetometer=(), "
                    b"microphone=(), "
                    b"payment=(), "
                    b"usb=()"
                )
                
                # Reconstruire les headers
                message["headers"] = [[k, v] for k, v in headers.items()]
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)