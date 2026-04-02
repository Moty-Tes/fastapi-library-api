# ============================================================================
# middleware.py
# ============================================================================
# PURPOSE: This file contains custom middleware and global error handlers
# 
# WHAT IS MIDDLEWARE?
# - Code that runs BEFORE every request and AFTER every request
# - Like a security checkpoint that every request must pass through
#
# WHAT ARE ERROR HANDLERS?
# - Catch errors from ANY endpoint and return consistent error messages
# - Without this, each error might look different to the user
#
# RELATED TO:
# - main.py: We register these handlers in the main app
# - All endpoints: Every request goes through LoggingMiddleware
# - All endpoints: Every error is caught by these handlers
# ============================================================================

import time
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse


# ============================================================================
# PART 1: LOGGING MIDDLEWARE
# ============================================================================
# WHAT THIS DOES:
# - Logs EVERY request that comes to your API
# - Shows: HTTP method (GET/POST), path (/books), status code (200/404)
# - Shows how long the request took (in seconds)
#
# WHEN THIS RUNS:
# - BEFORE your endpoint: logs "Request received"
# - AFTER your endpoint: logs "Response completed"
#
# WHY WE NEED THIS:
# - Debugging: See what requests are coming in
# - Performance: See which endpoints are slow
# - Monitoring: Track API usage
# ============================================================================

class LoggingMiddleware:
    """This middleware logs every request that comes to our API"""
    
    async def __call__(self, request: Request, call_next):
        """
        This is the function that runs for every request.
        
        PARAMETERS:
        - request: The incoming HTTP request (contains method, URL, headers)
        - call_next: Function that continues to the next middleware or endpoint
        
        RETURNS:
        - response: The HTTP response going back to the client
        """
        
        # ========== BEFORE THE REQUEST (Request arrives) ==========
        start_time = time.time()           # Record current time in seconds
        method = request.method             # GET, POST, PUT, PATCH, DELETE
        path = request.url.path             # /books, /books/42, /users/me
        
        # Print to terminal so you can see what's happening
        print(f"📥 Request: {method} {path} - received")
        
        # ========== PROCESS THE REQUEST (Go to your endpoint) ==========
        # This sends the request to the next middleware or to your endpoint
        # Your endpoint runs here and returns a response
        response = await call_next(request)
        
        # ========== AFTER THE REQUEST (Response is ready) ==========
        process_time = time.time() - start_time   # How many seconds it took
        status_code = response.status_code        # 200, 404, 500, etc.
        
        # Print to terminal with emoji for visual clarity
        if status_code >= 400:
            # Error status codes (404, 500) get a warning emoji
            print(f"⚠️ Response: {method} {path} - {status_code} in {process_time:.3f}s")
        else:
            # Success status codes (200, 201) get a checkmark
            print(f"✅ Response: {method} {path} - {status_code} in {process_time:.3f}s")
        
        # Add custom header to response (shows how long request took)
        response.headers["X-Process-Time"] = str(process_time)
        
        return response   # Send response back to the client


# ============================================================================
# PART 2: GLOBAL ERROR HANDLERS
# ============================================================================
# WHAT THIS DOES:
# - Catches ALL errors that happen in your endpoints
# - Returns a CONSISTENT error format every time
# - Without this, errors would look different (some plain text, some JSON)
#
# TWO TYPES OF ERRORS WE HANDLE:
# 1. HTTPException: Errors you intentionally raise (404, 400, 401)
# 2. Exception: Unexpected errors (bugs, crashes, division by zero)
#
# WHY WE NEED THIS:
# - Consistency: All errors look the same to the client
# - Security: Hide internal error details from users
# - Debugging: Log the real error for you (developer) but hide from users
# ============================================================================

def register_error_handlers(app):
    """
    Register all global error handlers with the FastAPI app.
    
    This function is called in main.py after creating the app:
        register_error_handlers(app)
    
    PARAMETERS:
    - app: The FastAPI application instance
    
    RETURNS:
    - Nothing (modifies the app in place)
    
    RELATED TO:
    - main.py: Where this function is called
    - All endpoints: Any error raised will be caught here
    """
    
    # ========== ERROR HANDLER 1: HTTP EXCEPTIONS ==========
    # This catches errors you intentionally raise, like:
    #   raise HTTPException(status_code=404, detail="Book not found")
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """
        Handles all HTTP exceptions (404, 400, 401, 403, 500, etc.)
        
        RETURNS: Consistent JSON error format with:
        - success: Always False for errors
        - error.code: HTTP status code (404, 400, etc.)
        - error.message: The error description
        - error.path: Which URL caused the error
        """
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                    "path": request.url.path
                }
            }
        )
    
    # ========== ERROR HANDLER 2: UNEXPECTED ERRORS ==========
    # This catches ANY error that wasn't an HTTPException
    # Examples: division by zero, list index out of range, type errors
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """
        Handles ANY uncaught exception (bugs in your code).
        
        IMPORTANT: In production (DEBUG=False), we hide the real error
        from users for security. Only the developer sees the real error
        in the terminal logs.
        """
        
        # Log the ACTUAL error to terminal (only you see this)
        print(f"💥 UNHANDLED ERROR: {type(exc).__name__} - {exc}")
        
        # Return a SAFE error message to the user (hide internal details)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {
                    "code": 500,
                    "message": "An internal server error occurred",
                    "path": request.url.path
                }
            }
        )


# ============================================================================
# WHAT I FORGOT TO TELL YOU EARLIER:
# ============================================================================
# 
# 1. __init__.py FILE:
#    - You need an empty file named __init__.py in the same folder
#    - Without it, Python doesn't recognize this folder as a package
#    - Create it with: New-Item -Path __init__.py -ItemType File
#
# 2. HOW TO USE THIS FILE IN main.py:
#    from middleware import LoggingMiddleware, register_error_handlers
#    
#    app.add_middleware(LoggingMiddleware)
#    register_error_handlers(app)
#
# 3. THE ORDER MATTERS:
#    - Middleware runs in the order you add them
#    - LoggingMiddleware should be first (to log everything)
#    - CORS middleware can be before or after (doesn't matter much)
#
# 4. WHAT YOU SEE IN TERMINAL:
#    📥 Request: GET /books - received
#    ✅ Response: GET /books - 200 in 0.015s
#    
#    📥 Request: GET /books/999 - received
#    ⚠️ Response: GET /books/999 - 404 in 0.008s
#    
#    💥 UNHANDLED ERROR: ZeroDivisionError - division by zero
#
# 5. THE X-Process-Time HEADER:
#    - Added to every response
#    - View it in browser's Developer Tools > Network tab
#    - Useful for debugging slow endpoints
# ============================================================================