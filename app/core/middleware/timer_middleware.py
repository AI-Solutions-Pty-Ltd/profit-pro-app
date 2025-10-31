# myapp/middleware/timer_middleware.py
import time


class RequestTimerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        end_time = time.time()
        request_time = end_time - start_time

        # You can now use 'request_time' for logging, adding a header, etc.
        # For example, adding it to the response header:
        response["X-Request-Time"] = f"{request_time:.4f}s"

        # Or logging it:
        # only print requests longer than 0.5 seconds
        if request_time > 0.5:
            print(f"Request to {request.path} took {request_time:.4f} seconds")

        return response
