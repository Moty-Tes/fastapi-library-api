# ==================================================================================
# FILE: main.py
# ==================================================================================
# 
# WHAT IS THIS FILE?
# ==================
# This is the MAIN ENTRY POINT of your entire API.
# EVERY request from the browser comes here first.
# 
# WHAT HAPPENS WHEN A REQUEST ARRIVES?
# ====================================
# 1. Browser sends request to https://your-api.onrender.com/books
# 2. Uvicorn (server) receives it
# 3. FastAPI looks at the URL (/books) and HTTP method (GET)
# 4. FastAPI finds the matching function below (@app.get("/books"))
# 5. That function runs and returns a response
# 6. Response goes back to the browser
#
# WHY IS THIS FILE IMPORTANT?
# ===========================
# Without this file, your API has NO endpoints.
# Nothing would respond to any URL.
#
# RELATED FILES:
# ==============
# - database.py: Provides database connection and models
# - config.py: Provides settings from .env file
# - middleware.py: Provides logging and error handling
# ==================================================================================

# ==================================================================================
# SECTION 1: IMPORTS (Bringing in tools from other files)
# ==================================================================================
# 
# WHY DO WE IMPORT?
# =================
# We don't want to write everything from scratch.
# We import pre-built tools that other developers made.
# Think of imports like borrowing tools from a toolbox.

from fastapi import FastAPI, HTTPException, status, Depends
# FastAPI: The main framework - creates your web app
# HTTPException: Used to return error responses (404 Not Found, 400 Bad Request)
# status: Provides HTTP status codes (200, 404, 500) instead of typing numbers
# Depends: A special FastAPI feature that runs code BEFORE your endpoint

from fastapi.middleware.cors import CORSMiddleware
# CORSMiddleware: Allows other websites to call your API
# Without this, browsers block requests from different domains

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# OAuth2PasswordBearer: Tells FastAPI "look for the token in the Authorization header"
# OAuth2PasswordRequestForm: A standard form for username/password login

from pydantic import BaseModel, EmailStr
# BaseModel: The foundation for ALL data validation
# EmailStr: Automatically checks if an email is valid (has @ and .com)

from typing import Optional, List
# Optional: Means a field can be None (for partial updates)
# List: Used when returning multiple items (like a list of books)

from sqlalchemy.orm import Session
# Session: Represents a conversation with the database
# Used to query, add, update, or delete data

from passlib.context import CryptContext
# CryptContext: Handles password hashing (encryption)
# Never store plain text passwords!

from datetime import datetime, timedelta
# datetime: Gets the current time
# timedelta: Represents a duration of time (like 30 minutes)

from jose import JWTError, jwt
# JWTError: Exception raised when a token is invalid
# jwt: Functions to create and verify JWT tokens

from database import SessionLocal, engine, get_db
# SessionLocal: Factory that creates database sessions
# engine: The actual connection to the database file
# get_db: A dependency that gives endpoints a database session

import database
# The entire database.py file - gives us BookDB, UserDB models

from config import settings
# settings: All configuration from .env file

from middleware import LoggingMiddleware, register_error_handlers
# LoggingMiddleware: Code that logs every request
# register_error_handlers: Sets up global error handling

# ==================================================================================
# SECTION 2: PASSWORD HASHING SETUP
# ==================================================================================
#
# WHAT IS PASSWORD HASHING?
# =========================
# Hashing converts a password into a fixed-length string that CANNOT be reversed.
# 
# EXAMPLE:
#   Password: "mysecret123"
#   Hashed:   "$2b$12$KxQ9mP2nQ5rT8vW1yZ4aB7cD0eF3gH6jL9oM2pR5sU8x"
#
# WHY HASH PASSWORDS?
# ===================
# If someone steals your database, they get hashed passwords, not real ones.
# They can't log in as users because they don't know the original passwords.
#
# HOW VERIFICATION WORKS:
# =======================
# When user logs in:
#   1. User enters "mysecret123"
#   2. We hash it using the SAME algorithm
#   3. Compare with stored hash
#   4. If they match → password is correct

# pwd_context is a tool that can hash passwords and verify them
# schemes=["bcrypt"] means use bcrypt (industry standard)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ==================================================================================
# SECTION 3: JWT (JSON Web Token) CONFIGURATION
# ==================================================================================
#
# WHAT IS JWT?
# ============
# JWT is a secure string that proves a user is logged in.
# Think of it like a movie ticket:
#   - Has your name (user ID)
#   - Has expiration time (30 minutes)
#   - Is signed with a secret key (can't be forged)
#
# JWT STRUCTURE:
# ==============
# eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.signature
# └──HEADER───┘.└───PAYLOAD────┘.└─SIGNATURE─┘
#   Algorithm      User data      Verification
#
# WHERE DOES SECRET_KEY COME FROM?
# ================================
# It comes from your .env file (not hardcoded in code!)
# This keeps it secret and different for production.

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"  # HS256 = HMAC with SHA-256 (standard for JWT)
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Token expires after 30 minutes

# ==================================================================================
# SECTION 4: CREATE FASTAPI APPLICATION
# ==================================================================================
#
# app = FastAPI() creates the main application object.
# This object is what Uvicorn runs when you start the server.
# The name "app" is expected by Uvicorn (uvicorn main:app)

app = FastAPI()

# ==================================================================================
# SECTION 5: MIDDLEWARE SETUP
# ==================================================================================
#
# WHAT IS MIDDLEWARE?
# ===================
# Middleware is code that runs for EVERY request, BEFORE and AFTER your endpoint.
#
# REQUEST FLOW:
# =============
# Browser → Uvicorn → LoggingMiddleware → CORS → Your Endpoint → Back
#                       ↓                    ↓         ↓
#                    Logs "req"          Adds      Does the
#                                       headers    actual work

# 1. Add logging middleware (runs first, logs everything)
app.add_middleware(LoggingMiddleware)

# 2. Add CORS middleware (allows other websites to call your API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # "*" = allow ANY website
    allow_credentials=True,     # Allow cookies and auth headers
    allow_methods=["*"],        # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],        # Allow all headers
)

# 3. Register error handlers (catch errors and return consistent format)
register_error_handlers(app)

# ==================================================================================
# SECTION 6: CREATE DATABASE TABLES
# ==================================================================================
#
# This creates all tables (books, users) in the SQLite database file.
# If tables already exist, it does nothing (safe to run multiple times).
# Base.metadata.create_all() tells SQLAlchemy to create all registered tables.

database.Base.metadata.create_all(bind=engine)

# ==================================================================================
# SECTION 7: PYDANTIC MODELS (Data Validation)
# ==================================================================================
#
# WHAT ARE PYDANTIC MODELS?
# =========================
# They define the SHAPE of data that your API accepts and returns.
# They automatically:
#   - Validate types (string, integer, etc.)
#   - Generate documentation for /docs
#   - Convert between JSON and Python objects

class Book(BaseModel):
    """Used when a client wants to CREATE a new book (no ID needed)"""
    title: str      # Must be text, cannot be empty
    author: str     # Must be text, cannot be empty
    year: int       # Must be a whole number
    price: float    # Can have decimals (29.99)

class BookUpdate(BaseModel):
    """Used when a client wants to PARTIALLY update a book (all fields optional)"""
    title: Optional[str] = None   # If provided, update title
    author: Optional[str] = None  # If provided, update author
    year: Optional[int] = None    # If provided, update year
    price: Optional[float] = None # If provided, update price

class BookResponse(BaseModel):
    """Used when sending book data BACK to the client (includes ID)"""
    id: int
    title: str
    author: str
    year: int
    price: float

class UserCreate(BaseModel):
    """Used when a client wants to REGISTER a new user"""
    username: str
    email: EmailStr   # EmailStr automatically validates format
    password: str     # Plain password (will be hashed before storing)

class UserResponse(BaseModel):
    """Used when sending user data BACK to the client (NO password!)"""
    id: int
    username: str
    email: str
    is_active: bool

class Token(BaseModel):
    """Response after successful login"""
    access_token: str   # The JWT token the client must save
    token_type: str     # Always "bearer" (standard OAuth2)

class TokenData(BaseModel):
    """What is stored INSIDE the JWT token (client never sees this)"""
    user_id: int
    username: str

# ==================================================================================
# SECTION 8: OAUTH2 SETUP (Authentication Configuration)
# ==================================================================================
#
# oauth2_scheme tells FastAPI:
#   - "Look for the token in the Authorization header"
#   - "If token is missing, return 401 Unauthorized"
#   - "The login endpoint is at /users/login"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

# ==================================================================================
# SECTION 9: DEPENDENCIES (Reusable Code)
# ==================================================================================
#
# A dependency is a function that runs BEFORE your endpoint.
# It can validate data, check permissions, or provide database connections.

def get_book_by_id(book_id: int, db: Session = Depends(get_db)):
    """
    DEPENDENCY: Checks if a book exists in the database.
    Used by GET, PUT, PATCH, DELETE /books/{book_id} endpoints.
    
    HOW IT WORKS:
    1. Gets book_id from the URL (e.g., /books/42)
    2. Queries the database for a book with that ID
    3. If found → returns the book object
    4. If not found → raises 404 error (stops execution)
    
    WHY IS THIS REUSABLE?
    Without this, every endpoint would need the same 5 lines of code.
    """
    book = db.query(database.BookDB).filter(database.BookDB.id == book_id).first()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    return book

# ==================================================================================
# SECTION 10: AUTHENTICATION HELPER FUNCTIONS
# ==================================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if the entered password matches the stored hash.
    Returns True if correct, False if not.
    """
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(db: Session, username: str, password: str):
    """
    Finds a user by username and verifies the password.
    Returns the user object if successful, False if not.
    """
    user = db.query(database.UserDB).filter(
        database.UserDB.username == username
    ).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Creates a new JWT token.
    The token contains user data (id, username) and an expiration time.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    DEPENDENCY: Validates the JWT token and returns the current user.
    Used by any endpoint that requires authentication.
    
    HOW IT WORKS:
    1. Gets token from Authorization header
    2. Decodes token using SECRET_KEY
    3. Extracts user_id from token
    4. Looks up user in database
    5. Returns user object (or 401 if invalid)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        username: str = payload.get("username")
        if user_id is None or username is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id, username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(database.UserDB).filter(database.UserDB.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    return user

# ==================================================================================
# SECTION 11: PUBLIC ENDPOINTS (No authentication required)
# ==================================================================================

@app.get("/")
async def root():
    """Homepage - anyone can see this"""
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
    List all books with optional filters.
    Anyone can see this (no login required).
    
    QUERY PARAMETERS:
    - skip: How many books to skip (for pagination)
    - limit: Maximum number of books to return
    - author: Filter by author name (partial match)
    - min_price: Minimum price filter
    - max_price: Maximum price filter
    """
    query = db.query(database.BookDB)
    if author:
        query = query.filter(database.BookDB.author.ilike(f"%{author}%"))
    query = query.filter(database.BookDB.price >= min_price)
    query = query.filter(database.BookDB.price <= max_price)
    books = query.offset(skip).limit(limit).all()
    return books

@app.get("/books/{book_id}", response_model=BookResponse)
async def get_book(book = Depends(get_book_by_id)):
    """Get a specific book by its ID. Anyone can see this."""
    return book

# ==================================================================================
# SECTION 12: AUTHENTICATION ENDPOINTS (Login, Register)
# ==================================================================================

@app.post("/users/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account.
    Anyone can register (no login required).
    
    STEPS:
    1. Check if username already exists
    2. Check if email already exists
    3. Hash the password
    4. Save user to database
    5. Return user info (without password)
    """
    # Check username
    existing_username = db.query(database.UserDB).filter(
        database.UserDB.username == user.username
    ).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Check email
    existing_email = db.query(database.UserDB).filter(
        database.UserDB.email == user.email
    ).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password and save
    hashed_password = pwd_context.hash(user.password)
    db_user = database.UserDB(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_active=1
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserResponse(
        id=db_user.id,
        username=db_user.username,
        email=db_user.email,
        is_active=bool(db_user.is_active)
    )

@app.post("/users/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login endpoint - returns a JWT token.
    Anyone can login (no token needed to get a token).
    
    The client must send:
    - username: their username
    - password: their password
    
    The response contains an access_token that must be used for protected endpoints.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """
    Get information about the currently logged-in user.
    This endpoint REQUIRES authentication (valid JWT token).
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=bool(current_user.is_active)
    )

# ==================================================================================
# SECTION 13: PROTECTED BOOK ENDPOINTS (Require authentication)
# ==================================================================================

@app.post("/books", status_code=status.HTTP_201_CREATED, response_model=BookResponse)
async def create_book(
    book: Book,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)  # <-- REQUIRES LOGIN!
):
    """Create a new book. You must be logged in to do this."""
    db_book = database.BookDB(
        title=book.title,
        author=book.author,
        year=book.year,
        price=book.price
    )
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.put("/books/{book_id}", response_model=BookResponse)
async def update_book(
    book: Book,
    db_book = Depends(get_book_by_id),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)  # <-- REQUIRES LOGIN!
):
    """Completely replace a book. You must be logged in."""
    db_book.title = book.title
    db_book.author = book.author
    db_book.year = book.year
    db_book.price = book.price
    db.commit()
    db.refresh(db_book)
    return db_book

@app.patch("/books/{book_id}", response_model=BookResponse)
async def partial_update_book(
    book_update: BookUpdate,
    db_book = Depends(get_book_by_id),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)  # <-- REQUIRES LOGIN!
):
    """Partially update a book (only send fields that changed). You must be logged in."""
    if book_update.title is not None:
        db_book.title = book_update.title
    if book_update.author is not None:
        db_book.author = book_update.author
    if book_update.year is not None:
        db_book.year = book_update.year
    if book_update.price is not None:
        db_book.price = book_update.price
    db.commit()
    db.refresh(db_book)
    return db_book

@app.delete("/books/{book_id}", status_code=status.HTTP_200_OK)
async def delete_book(
    db_book = Depends(get_book_by_id),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)  # <-- REQUIRES LOGIN!
):
    """Delete a book. You must be logged in."""
    db.delete(db_book)
    db.commit()
    return {
        "message": "Book deleted successfully!",
        "book_id": db_book.id,
        "deleted_book": {
            "title": db_book.title,
            "author": db_book.author
        }
    }