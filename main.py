# ==================================================================================
# FILE: main.py
# ==================================================================================
# 
# WHAT IS THIS FILE?
# ==================
# This is the HEART of your entire API. Every request from the browser 
# comes to this file first. It decides:
#   - Which endpoint to run (based on URL and HTTP method)
#   - What data to validate (using Pydantic models)
#   - Which database operations to perform (using SQLAlchemy)
#   - What response to send back
#
# WHY IS IT CALLED main.py?
# =========================
# By convention, the main entry point of a Python application is called main.py
# When we run `uvicorn main:app`, we're telling Uvicorn:
#   - Look for a file called "main.py"
#   - Inside it, find a variable named "app"
#   - Run that as the web application
#
# WHAT HAPPENS WHEN A REQUEST ARRIVES?
# ====================================
# Browser Request → Uvicorn (server) → main.py → Middleware → Endpoint → Response
#                      ↓                    ↓           ↓           ↓
#                   Listens on            Routes     Logs the    Does the
#                   port 8000             the URL    request     actual work
#
# RELATED FILES:
# ==============
# - database.py:    Provides database connection and table models
# - config.py:      Provides settings from .env file (secrets, app name, etc.)
# - middleware.py:  Provides logging and error handling
# - .env:           Stores secrets (database URL, secret key)
# - library.db:     SQLite database file (created by SQLAlchemy)
# ==================================================================================


# ==================================================================================
# SECTION 1: IMPORTS (Bringing in external code)
# ==================================================================================
# WHAT ARE IMPORTS?
# =================
# Imports bring code from other files into this one. Think of them like:
#   - Borrowing tools from other people's toolboxes
#   - Using pre-built lego pieces instead of making everything from scratch
#
# WHY DO WE NEED THEM?
# ====================
# Without imports, you'd have to write EVERYTHING yourself:
#   - Web server (1000+ lines)
#   - Database connection (500+ lines)
#   - Password encryption (300+ lines)
#   - JWT token creation (200+ lines)
#
# Instead, we import battle-tested libraries that do all this for us!
# ==================================================================================

# ---------- FastAPI Core ----------
# These are the main FastAPI tools we use throughout the file
from fastapi import FastAPI, HTTPException, status, Depends
# FastAPI:        The main framework class - we create an instance of this
# HTTPException:  Used to return error responses (404 Not Found, 400 Bad Request)
# status:         Provides HTTP status codes (200, 201, 404, 500) - cleaner than typing numbers
# Depends:        Used for dependency injection - runs code before your endpoint

# ---------- CORS (Cross-Origin Resource Sharing) ----------
# Allows other websites to call your API
# Without this, browsers block requests from different domains
from fastapi.middleware.cors import CORSMiddleware
# CORSMiddleware: Adds headers to responses telling browsers "it's OK to call this API"

# ---------- Security / Authentication ----------
# Tools for user login and token management
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# OAuth2PasswordBearer:   Tells FastAPI where to find the login endpoint
# OAuth2PasswordRequestForm: A standard form for username/password login

# ---------- Pydantic (Data Validation) ----------
# Validates that incoming data has the correct shape and types
from pydantic import BaseModel, EmailStr
# BaseModel:   The base class for ALL data models - validates data automatically
# EmailStr:    Special string type that validates email format (must contain @ and .)

# ---------- Python Type Hints ----------
# These don't affect runtime behavior, but help with code completion and catching bugs
from typing import Optional, List
# Optional:    Means a field can be None (for partial updates)
# List:        Used when returning a list of items (e.g., multiple books)

# ---------- SQLAlchemy (Database) ----------
# Talks to the database and converts between Python objects and SQL
from sqlalchemy.orm import Session
# Session:     A conversation with the database - used to query, add, update, delete

# ---------- Passlib (Password Hashing) ----------
# Encrypts passwords so they're never stored in plain text
from passlib.context import CryptContext
# CryptContext: A tool that handles password hashing and verification

# ---------- DateTime (Time handling) ----------
# Used to set expiration times on JWT tokens
from datetime import datetime, timedelta
# datetime:    Current time
# timedelta:   Amount of time (e.g., 30 minutes from now)

# ---------- JWT (JSON Web Tokens) ----------
# Creates and verifies secure tokens for authentication
from jose import JWTError, jwt
# JWTError:    Exception when token is invalid
# jwt:         Functions to encode (create) and decode (verify) tokens

# ---------- Local Imports (Your own files!) ----------
# These are files YOU created in this project
from database import SessionLocal, engine, get_db
# SessionLocal: Factory that creates database sessions
# engine:       The actual connection to the database file
# get_db:       A dependency that gives endpoints a database session

import database
# database:     The entire database.py file - gives us access to BookDB, UserDB models

from config import settings
# settings:     All configuration from .env file (app name, secret key, etc.)

from middleware import LoggingMiddleware, register_error_handlers
# LoggingMiddleware:       Custom code that logs every request
# register_error_handlers: Function that sets up global error handling


# ==================================================================================
# SECTION 2: PASSWORD HASHING SETUP
# ==================================================================================
# WHAT IS PASSWORD HASHING?
# ========================
# Hashing converts a password into a fixed-length string that CANNOT be reversed.
# 
# Example:
#   Password: "mysecret123"
#   Hashed:   "$2b$12$KxQ...encrypted_string..."
#
# WHY NOT STORE PLAIN TEXT PASSWORDS?
# ===================================
# If someone steals your database, they get ALL passwords!
# With hashing, they only get garbage that can't be turned back into passwords.
#
# HOW DOES VERIFICATION WORK?
# ===========================
# When user logs in:
#   1. User enters password: "mysecret123"
#   2. We hash it using the SAME algorithm
#   3. Compare the hash with stored hash
#   4. If they match → password is correct
#
# WHAT IS bcrypt?
# ===============
# bcrypt is a hashing algorithm designed to be SLOW (on purpose!)
# Slow hashing makes brute-force attacks impractical
# ==================================================================================

# pwd_context: A tool that can hash passwords and verify them
# schemes=["bcrypt"]: Use bcrypt algorithm (industry standard)
# deprecated="auto": Automatically handle old hash formats
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==================================================================================
# SECTION 3: JWT (JSON Web Token) CONFIGURATION
# ==================================================================================
# WHAT IS JWT?
# ============
# JWT is a secure string that proves a user is logged in.
# Think of it like a movie ticket:
#   - Contains user info (like your name on the ticket)
#   - Has an expiration time (ticket valid for 2 hours)
#   - Is signed with a secret key (special stamp that can't be forged)
#
# JWT STRUCTURE:
# ==============
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidXNlcm5hbWUiOiJtb3R5In0.signature
# └─────────HEADER─────────┘.└──────────PAYLOAD───────────┘.└─SIGNATURE─┘
#   Algorithm info              User data (id, username)     Verification stamp
#
# WHAT IS SECRET_KEY?
# ===================
# A secret key is like a password used to sign tokens.
# Only the server knows it! If someone steals it, they can forge tokens.
# That's why we keep it in .env file (not in code!)
# ==================================================================================

# Get secret key from .env file (never hardcode secrets!)
SECRET_KEY = settings.SECRET_KEY

# Algorithm for signing tokens
# HS256 = HMAC with SHA-256 (industry standard for JWT)
ALGORITHM = "HS256"

# How long until token expires (30 minutes)
# After this, user must log in again
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# ==================================================================================
# SECTION 4: CREATE FASTAPI APPLICATION
# ==================================================================================
# WHAT DOES app = FastAPI() DO?
# =============================
# Creates the main application object that:
#   - Listens for requests on specific URLs
#   - Routes requests to the correct function
#   - Handles errors
#   - Generates the /docs page
#
# WHY IS THIS VARIABLE NAMED "app"?
# =================================
# Uvicorn expects to find a variable named "app"
# When we run `uvicorn main:app`, it looks for "app" in "main.py"
# You could name it anything, but "app" is the convention
# ==================================================================================

app = FastAPI()


# ==================================================================================
# SECTION 5: MIDDLEWARE SETUP
# ==================================================================================
# WHAT IS MIDDLEWARE?
# ==================
# Middleware is code that runs for EVERY request, before AND after your endpoint.
# 
# REQUEST FLOW WITH MIDDLEWARE:
# =============================
# Browser → Uvicorn → Middleware 1 → Middleware 2 → Endpoint → Middleware 2 → Middleware 1 → Browser
#                      ↓              ↓             ↓           ↓              ↓             ↓
#                   Logs "req"     CORS adds     Your code    Your code     CORS adds     Logs "resp"
#                                  headers                    runs          headers
#
# ORDER MATTERS!
# ==============
# Middleware runs in the order you add them.
# We add LoggingMiddleware first because we want to log EVERYTHING.
# ==================================================================================

# ---------- Middleware 1: Logging Middleware ----------
# This runs for every request and logs details to terminal
# Added first so it wraps everything else
app.add_middleware(LoggingMiddleware)

# ---------- Middleware 2: CORS Middleware ----------
# This adds headers to responses telling browsers "it's OK to call this API"
# Without this, browsers block requests from other domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # "*" = allow ANY website (change in production!)
    allow_credentials=True,     # Allow cookies and auth headers
    allow_methods=["*"],        # Allow all HTTP methods (GET, POST, PUT, etc.)
    allow_headers=["*"],        # Allow all headers
)

# ---------- Global Error Handlers ----------
# These catch ANY error from ANY endpoint and return consistent JSON
# Without this, errors would look different (some plain text, some JSON)
register_error_handlers(app)


# ==================================================================================
# SECTION 6: DATABASE TABLE CREATION
# ==================================================================================
# WHAT DOES THIS DO?
# ==================
# Creates ALL tables defined in database.py (books table, users table)
# in the SQLite database file (library.db)
#
# WHY IS THIS HERE?
# =================
# When the app starts, we want to make sure tables exist.
# If they don't exist, create them.
# If they already exist, do nothing (safe to run multiple times)
#
# WHAT IS Base?
# =============
# Base is from database.py - it's a registry of all table classes
# Base.metadata.create_all() tells SQLAlchemy to create all registered tables
# ==================================================================================

database.Base.metadata.create_all(bind=engine)


# ==================================================================================
# SECTION 7: PYDANTIC MODELS (Data Validation)
# ==================================================================================
# WHAT ARE PYDANTIC MODELS?
# =========================
# They define the SHAPE of data that your API accepts and returns.
# 
# WHY DO WE NEED THEM?
# ====================
# 1. Validation: Automatically check that data has correct types
# 2. Documentation: Automatically appear in /docs
# 3. Type hints: IDE knows what fields exist
# 4. Serialization: Convert between Python objects and JSON
#
# THREE TYPES OF MODELS IN THIS API:
# ==================================
# 1. Book:        What client sends to CREATE a book (no ID)
# 2. BookUpdate:  What client sends to PARTIALLY update (all optional)
# 3. BookResponse:What server returns when client READS a book (has ID)
#
# WHY SEPARATE MODELS FOR INPUT AND OUTPUT?
# =========================================
# - Input (Book):      No ID (database generates it)
# - Output (BookResponse): Has ID (client needs to know which book)
# - Update (BookUpdate): All fields optional (only send what changed)
# ==================================================================================

# ---------- BOOK MODELS ----------

class Book(BaseModel):
    """
    WHAT: Data required to CREATE a new book
    WHEN: Used in POST /books endpoint
    WHERE: Client sends this JSON in request body
    WHY NO ID? Database generates ID automatically
    
    EXAMPLE REQUEST:
    {
        "title": "Python Basics",
        "author": "John Smith",
        "year": 2020,
        "price": 29.99
    }
    """
    title: str      # Book title - required, must be text
    author: str     # Author name - required, must be text
    year: int       # Publication year - required, must be whole number
    price: float    # Price - required, can have decimals (29.99)

class BookUpdate(BaseModel):
    """
    WHAT: Data to PARTIALLY update a book
    WHEN: Used in PATCH /books/{book_id} endpoint
    WHY ALL OPTIONAL? Client can update just ONE field
    
    EXAMPLE REQUEST (update only price):
    {
        "price": 39.99
    }
    
    EXAMPLE REQUEST (update title and author):
    {
        "title": "New Title",
        "author": "New Author"
    }
    """
    title: Optional[str] = None     # Optional - if provided, update title
    author: Optional[str] = None    # Optional - if provided, update author
    year: Optional[int] = None      # Optional - if provided, update year
    price: Optional[float] = None   # Optional - if provided, update price

class BookResponse(BaseModel):
    """
    WHAT: Data returned when client READS a book
    WHEN: Used in GET /books and GET /books/{book_id}
    WHY HAS ID? Client needs to know which book this is for updates/deletes
    
    EXAMPLE RESPONSE:
    {
        "id": 1,
        "title": "Python Basics",
        "author": "John Smith",
        "year": 2020,
        "price": 29.99
    }
    """
    id: int         # Unique identifier (from database)
    title: str      # Book title
    author: str     # Author name
    year: int       # Publication year
    price: float    # Price


# ---------- USER MODELS ----------

class UserCreate(BaseModel):
    """
    WHAT: Data required to REGISTER a new user
    WHEN: Used in POST /users/register
    WHERE: Client sends this JSON in request body
    
    WHY EmailStr? Automatically validates email format
    WHY password separate? We hash it before storing
    
    EXAMPLE REQUEST:
    {
        "username": "moty",
        "email": "moty@example.com",
        "password": "mysecret123"
    }
    """
    username: str                  # Username - must be unique
    email: EmailStr                # Email - automatically validates format (@ and .)
    password: str                  # Plain password (will be hashed before storing)

class UserResponse(BaseModel):
    """
    WHAT: Data returned after registration or login
    WHEN: Used in POST /users/register and GET /users/me
    WHY NO PASSWORD? Security! Never send passwords back to client
    
    EXAMPLE RESPONSE:
    {
        "id": 1,
        "username": "moty",
        "email": "moty@example.com",
        "is_active": true
    }
    """
    id: int          # User ID from database
    username: str    # Username
    email: str       # Email address
    is_active: bool  # Whether account is enabled (true/false)

class Token(BaseModel):
    """
    WHAT: Response after successful login
    WHEN: Used in POST /users/login
    WHY token_type "bearer"? Standard OAuth2 format
    
    EXAMPLE RESPONSE:
    {
        "access_token": "eyJhbGciOiJIUzI1NiIs...",
        "token_type": "bearer"
    }
    """
    access_token: str   # The JWT token (client must send this with protected requests)
    token_type: str     # Always "bearer" (standard OAuth2)

class TokenData(BaseModel):
    """
    WHAT: Data stored INSIDE the JWT token
    WHEN: Used when creating and decoding tokens
    WHY NOT SENT TO CLIENT? This is internal - client never sees this
    
    WHAT'S INSIDE THE TOKEN:
    The token contains this data PLUS expiration time
    """
    user_id: int        # User ID (to look up in database)
    username: str       # Username (for quick access)


# ==================================================================================
# SECTION 8: OAUTH2 SETUP (Authentication Configuration)
# ==================================================================================
# WHAT IS OAuth2PasswordBearer?
# =============================
# This tells FastAPI:
#   - "Look for the token in the Authorization header"
#   - "If token is missing, return 401 Unauthorized"
#   - "The login endpoint is at /users/login"
#
# HOW CLIENT SENDS TOKEN:
# =======================
# Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
#                ↑       ↑
#                Type    Token
#
# WHY DO WE NEED THIS?
# ====================
# Without this, FastAPI wouldn't know where to find the token
# or where to redirect unauthenticated users
# ==================================================================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


# ==================================================================================
# SECTION 9: DEPENDENCIES (Reusable Code)
# ==================================================================================
# WHAT ARE DEPENDENCIES?
# ======================
# Dependencies are reusable pieces of code that run BEFORE your endpoint.
# They can:
#   - Validate data (e.g., check if book exists)
#   - Provide database connections
#   - Authenticate users
#
# WHY USE DEPENDENCIES?
# =====================
# Without dependencies, you'd write the same code in EVERY endpoint:
# 
#   # Without dependency (BAD - code duplication)
#   @app.get("/books/{id}")
#   def get_book(book_id):
#       book = db.query(Book).filter(Book.id == book_id).first()
#       if not book:
#           raise HTTPException(404)
#       return book
#   
#   @app.put("/books/{id}")
#   def update_book(book_id):
#       book = db.query(Book).filter(Book.id == book_id).first()  # DUPLICATED!
#       if not book:                                               # DUPLICATED!
#           raise HTTPException(404)                               # DUPLICATED!
#       # ... update logic
#
# With dependency, you write the check ONCE and reuse it everywhere!
# ==================================================================================

def get_book_by_id(book_id: int, db: Session = Depends(get_db)):
    """
    WHAT: Dependency that checks if a book exists
    WHEN: Used in GET, PUT, PATCH, DELETE /books/{book_id}
    WHY: Avoids writing the same "check if exists" code 4 times
    
    HOW IT WORKS:
    1. Gets book_id from URL path
    2. Gets database session from get_db dependency
    3. Queries database for book with that ID
    4. If not found → raises 404 error (stops execution)
    5. If found → returns the book object
    
    WHERE IT'S USED:
    - GET /books/{book_id}: Get and return the book
    - PUT /books/{book_id}: Update the book
    - PATCH /books/{book_id}: Partially update the book
    - DELETE /books/{book_id}: Delete the book
    
    RELATIONSHIPS:
    - Called by: Endpoints that need a book by ID
    - Calls: get_db (to get database session)
    - Uses: BookDB model from database.py
    """
    # Query database for book with matching ID
    # .first() returns the first result or None if not found
    book = db.query(database.BookDB).filter(database.BookDB.id == book_id).first()
    
    # If book doesn't exist, raise 404 error
    # This stops execution immediately - endpoint code won't run
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    # If book exists, return it to the endpoint
    return book


# ==================================================================================
# SECTION 10: AUTHENTICATION HELPER FUNCTIONS
# ==================================================================================
# WHAT DO THESE DO?
# =================
# These are internal functions that handle the authentication logic.
# They are NOT endpoints (no @app decorator).
# They are called by the login endpoint.
#
# WHY SEPARATE THEM?
# ==================
# Keeps the login endpoint clean and readable
# Makes it easy to test each piece individually
# Can be reused elsewhere if needed
# ==================================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    WHAT: Checks if entered password matches stored hash
    WHEN: Called by authenticate_user() during login
    WHY: We can't compare plain text to hash directly
    
    HOW IT WORKS:
    1. User enters password: "mysecret123"
    2. We have stored hash: "$2b$12$KxQ..."
    3. pwd_context.verify() hashes the entered password using same algorithm
    4. Compares the result with stored hash
    5. Returns True if match, False if not
    
    RETURNS: True if password matches, False otherwise
    
    RELATED TO:
    - pwd_context (from passlib)
    - authenticate_user() (calls this)
    """
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(db: Session, username: str, password: str):
    """
    WHAT: Finds user by username and verifies password
    WHEN: Called by login endpoint
    WHY: Combines two operations: find user + verify password
    
    HOW IT WORKS:
    1. Search database for user with matching username
    2. If user not found → return False
    3. If user found → verify password
    4. If password wrong → return False
    5. If all good → return user object
    
    RETURNS: User object if authenticated, False if not
    
    RELATIONSHIPS:
    - Called by: login endpoint
    - Calls: verify_password()
    - Uses: UserDB model from database.py
    """
    # Step 1: Find user by username
    user = db.query(database.UserDB).filter(
        database.UserDB.username == username
    ).first()
    
    # Step 2: If user doesn't exist, authentication fails
    if not user:
        return False
    
    # Step 3: Check if password matches
    if not verify_password(password, user.hashed_password):
        return False
    
    # Step 4: All good, return user
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    WHAT: Creates a new JWT token
    WHEN: Called by login endpoint after successful authentication
    WHY: Returns a token the client can use for protected endpoints
    
    HOW IT WORKS:
    1. Copy the data (user id, username) we want in token
    2. Calculate expiration time (now + expires_delta)
    3. Add expiration to the token data
    4. Sign the token with secret key (prevents tampering)
    5. Return the encoded token string
    
    WHAT'S IN THE TOKEN:
    - sub: user id (standard JWT field for subject)
    - username: user's username
    - exp: expiration timestamp
    
    TOKEN EXAMPLE (decoded):
    {
        "sub": 1,
        "username": "moty",
        "exp": 1734567890
    }
    
    RELATIONSHIPS:
    - Called by: login endpoint
    - Uses: SECRET_KEY, ALGORITHM from config
    - Returns: String that client must save
    """
    # Make a copy so we don't modify original
    to_encode = data.copy()
    
    # Calculate expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Default 15 minutes if not specified
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    # Add expiration to token data
    to_encode.update({"exp": expire})
    
    # Encode (create) the token with secret key
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    WHAT: Validates JWT token and returns current user
    WHEN: Used as dependency in protected endpoints
    WHY: Ensures only logged-in users can access certain endpoints
    
    HOW IT WORKS:
    1. Get token from Authorization header (oauth2_scheme does this)
    2. Decode token using secret key
    3. Extract user_id and username from token
    4. Look up user in database
    5. If any step fails → return 401 Unauthorized
    6. If all good → return user object
    
    WHERE IT'S USED:
    - POST /books (create book)
    - PUT /books/{id} (update book)
    - PATCH /books/{id} (partial update)
    - DELETE /books/{id} (delete book)
    - GET /users/me (get current user)
    
    RELATIONSHIPS:
    - Called by: Protected endpoints (via Depends())
    - Calls: oauth2_scheme (gets token from header)
    - Calls: get_db (gets database session)
    - Uses: SECRET_KEY, ALGORITHM to decode token
    - Returns: UserDB object from database
    """
    # This exception is raised if token is invalid
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode token (verify signature and extract data)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extract user ID and username from token
        user_id: int = payload.get("sub")
        username: str = payload.get("username")
        
        # If either is missing, token is invalid
        if user_id is None or username is None:
            raise credentials_exception
        
        # Create TokenData object (just for type safety)
        token_data = TokenData(user_id=user_id, username=username)
        
    except JWTError:
        # Token is malformed or tampered with
        raise credentials_exception
    
    # Look up user in database
    user = db.query(database.UserDB).filter(
        database.UserDB.id == token_data.user_id
    ).first()
    
    # If user doesn't exist (maybe deleted after token was issued)
    if user is None:
        raise credentials_exception
    
    # Return user object to the endpoint
    return user


# ==================================================================================
# SECTION 11: PUBLIC ENDPOINTS (No authentication required)
# ==================================================================================
# WHAT ARE PUBLIC ENDPOINTS?
# ==========================
# Anyone can access these, even without logging in.
# They only READ data, never modify it (GET requests).
#
# WHY ARE THEY PUBLIC?
# ====================
# - Homepage: Should be visible to everyone
# - Listing books: Anyone should see what books are available
# - Getting a specific book: Anyone can read book details
# ==================================================================================

@app.get("/")
async def root():
    """
    ENDPOINT: GET /
    PURPOSE: Homepage - shows API information
    AUTH: Not required (public)
    RETURNS: JSON with app name, version, debug mode, database URL
    
    WHEN IS THIS CALLED?
    - User visits http://127.0.0.1:8000/
    - First thing they see to understand what the API is
    
    RESPONSE EXAMPLE:
    {
        "message": "Welcome to My Library API!",
        "version": "1.0.0",
        "debug_mode": true,
        "database": "sqlite:///./library.db"
    }
    
    RELATIONSHIPS:
    - Uses: settings from config.py (APP_NAME, API_VERSION, etc.)
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}!",
        "version": settings.API_VERSION,
        "debug_mode": settings.DEBUG,
        "database": settings.DATABASE_URL
    }

@app.get("/books", response_model=List[BookResponse])
async def list_books(
    skip: int = 0,
    limit: int = 10,
    author: str = None,
    min_price: float = 0,
    max_price: float = 100,
    db: Session = Depends(get_db)
):
    """
    ENDPOINT: GET /books
    PURPOSE: List all books with optional filters
    AUTH: Not required (public)
    
    QUERY PARAMETERS:
    - skip: How many books to skip (for pagination) - default 0
    - limit: Maximum number of books to return - default 10
    - author: Filter by author name (partial match) - optional
    - min_price: Minimum price filter - default 0
    - max_price: Maximum price filter - default 100
    
    EXAMPLE REQUESTS:
    - GET /books                          → First 10 books
    - GET /books?skip=10&limit=5          → Books 11-15
    - GET /books?author=John              → Books by authors containing "John"
    - GET /books?min_price=20&max_price=50 → Books between $20-$50
    - GET /books?author=Jane&min_price=30 → Jane's books over $30
    
    HOW IT WORKS:
    1. Start with query for all books
    2. Apply author filter if provided (ilike = case-insensitive partial match)
    3. Apply price range filters
    4. Apply pagination (skip/limit)
    5. Execute query and return results
    
    RESPONSE EXAMPLE:
    [
        {"id": 1, "title": "Python Basics", "author": "John Smith", "year": 2020, "price": 29.99},
        {"id": 2, "title": "FastAPI Mastery", "author": "Jane Doe", "year": 2023, "price": 39.99}
    ]
    
    RELATIONSHIPS:
    - Calls: get_db (database session)
    - Uses: BookDB model from database.py
    - Returns: List of BookResponse models
    """
    # Start with query for all books
    query = db.query(database.BookDB)
    
    # Apply author filter (if provided)
    # ilike = case-insensitive like (matches partial strings)
    # f"%{author}%" means "contains author anywhere in the string"
    if author:
        query = query.filter(database.BookDB.author.ilike(f"%{author}%"))
    
    # Apply price filters
    query = query.filter(database.BookDB.price >= min_price)
    query = query.filter(database.BookDB.price <= max_price)
    
    # Apply pagination and execute query
    books = query.offset(skip).limit(limit).all()
    
    return books

@app.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book = Depends(get_book_by_id)):
    """
    ENDPOINT: GET /books/{book_id}
    PURPOSE: Get a specific book by its ID
    AUTH: Not required (public)
    
    PATH PARAMETER:
    - book_id: The ID of the book to retrieve
    
    EXAMPLE REQUEST:
    GET /books/42
    
    HOW IT WORKS:
    1. get_book_by_id dependency checks if book exists
    2. If exists, returns the book
    3. If not, returns 404 error
    
    RESPONSE EXAMPLE:
    {
        "id": 1,
        "title": "Python Basics",
        "author": "John Smith",
        "year": 2020,
        "price": 29.99
    }
    
    RELATIONSHIPS:
    - Uses: get_book_by_id dependency (checks existence)
    - Returns: BookResponse model
    """
    # get_book_by_id already validated the book exists
    # We just return it (FastAPI converts to BookResponse automatically)
    return book


# ==================================================================================
# SECTION 12: AUTHENTICATION ENDPOINTS
# ==================================================================================
# WHAT ARE THESE?
# ===============
# These endpoints handle user registration, login, and profile access.
# They don't require authentication themselves (except /users/me).
#
# WHY SEPARATE FROM BOOK ENDPOINTS?
# =================================
# These deal with USERS, not books.
# Keeps the code organized by responsibility.
# ==================================================================================

@app.post("/users/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    ENDPOINT: POST /users/register
    PURPOSE: Create a new user account
    AUTH: Not required (anyone can register)
    
    REQUEST BODY (UserCreate):
    {
        "username": "moty",
        "email": "moty@example.com",
        "password": "mysecret123"
    }
    
    HOW IT WORKS:
    1. Check if username already taken → if yes, error 400
    2. Check if email already registered → if yes, error 400
    3. Hash the password (never store plain text!)
    4. Create user in database
    5. Return user info (without password)
    
    RESPONSE EXAMPLE:
    {
        "id": 1,
        "username": "moty",
        "email": "moty@example.com",
        "is_active": true
    }
    
    SECURITY NOTES:
    - Password is hashed BEFORE storing
    - Password is NEVER returned in response
    - Username and email must be unique
    
    RELATIONSHIPS:
    - Calls: get_db (database session)
    - Calls: pwd_context.hash() (password encryption)
    - Uses: UserCreate model (input validation)
    - Uses: UserResponse model (output format)
    - Uses: UserDB model from database.py
    """
    
    # STEP 1: Check if username already exists
    existing_username = db.query(database.UserDB).filter(
        database.UserDB.username == user.username
    ).first()
    
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # STEP 2: Check if email already exists
    existing_email = db.query(database.UserDB).filter(
        database.UserDB.email == user.email
    ).first()
    
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # STEP 3: Hash the password (never store plain