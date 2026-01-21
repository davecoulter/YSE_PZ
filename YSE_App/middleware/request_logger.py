# YSE_App/middleware/request_logger.py

class RequestLoggingMiddleware:
    """
    Middleware to log incoming requests BEFORE Django parses them.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        print("\n=== Incoming Request ===")
        print(f"METHOD: {request.method}")
        print(f"CONTENT-TYPE: {request.content_type}")
        try:
            body_text = request.body.decode('utf-8')
            print(f"BODY RAW: {body_text}")
        except Exception as e:
            print(f"BODY could not be decoded: {e}")
        print("========================\n")
        return self.get_response(request)
