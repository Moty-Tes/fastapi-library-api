# ==================================================================================
# FILE: database.py
# ==================================================================================
#
# WHAT IS THIS FILE?
# ==================
# This file handles EVERYTHING related to your database:
#   - Connecting to the database file
#   - Defining what tables look like (Book table, User table)
#   - Creating database sessions (conversations with the database)
#   - Providing database connections to your endpoints
#
# WHY DO WE NEED A SEPARATE DATABASE FILE?
# ========================================
# Without this file, all database code would be inside main.py.
# That would make main.py HUGE and hard to maintain.
# Separating it keeps things organized:
#   - main.py: Handles API endpoints (what users can do)
#   - database.py: Handles database operations (how data is stored)
#
# WHAT IS SQLALCHEMY?
# ===================
# SQLAlchemy is an "ORM" (Object Relational Mapper).
# It lets you talk to databases using Python code instead of writing SQL.
#
# WITHOUT SQLAlchemy (raw SQL):
#   cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
#
# WITH SQLAlchemy (Python objects):
#   book = db.query(BookDB).filter(BookDB.id == book_id).first()
#
# The second is much more Pythonic and less error-prone!
#
# WHAT IS SQLITE?
# ===============
# SQLite is a lightweight database that stores everything in ONE file.
# No server to install, no configuration needed.
# Perfect for learning and small projects.
#
# WHAT HAPPENS WHEN YOU RUN THIS FILE?
# ====================================
# 1. Connects to library.db (creates it if doesn't exist)
# 2. Defines BookDB and UserDB classes (table structures)
# 3. Creates the actual tables in library.db
# 4. Provides get_db() function for endpoints to use
#
# RELATIONSHIPS:
# ==============
# - main.py:      Imports get_db, engine, SessionLocal, BookDB, UserDB
# - config.py:    Provides DATABASE_URL from .env file
# - .env:         Contains DATABASE_URL (sqlite:///./library.db)
# - library.db:   The actual database file (auto-created)
# ==================================================================================


# ==================================================================================
# SECTION 1: IMPORTS (What we need from external libraries)
# ==================================================================================
#
# WHY THESE SPECIFIC IMPORTS?
# ===========================
# We need different tools for different database tasks:
#   - create_engine:    Connect to the database file
#   - declarative_base: Create table classes
#   - sessionmaker:     Create database sessions
#   - Column, Integer, String, Float: Define table columns
#   - os, load_dotenv:  Read .env file for database URL
# ==================================================================================

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session


# ==================================================================================
# SECTION 2: LOAD ENVIRONMENT VARIABLES
# ==================================================================================
#
# WHAT DOES load_dotenv() DO?
# ============================
# It reads the .env file in your project folder and loads all key=value pairs
# into environment variables that Python can access with os.getenv().
#
# WHAT'S IN THE .env FILE?
# ========================
# DATABASE_URL=sqlite:///./library.db
# APP_NAME=My Library API
# DEBUG=True
# SECRET_KEY=your-secret-key
#
# WHY NOT HARDCODE DATABASE URL?
# ===============================
# - Different environments (development, testing, production) need different databases
# - You might switch from SQLite to PostgreSQL later
# - Hardcoding makes the code less flexible
# - .env file is NOT committed to Git (keeps configuration separate)
# ==================================================================================

# Load all variables from .env file into environment variables
# This must run BEFORE we try to read DATABASE_URL
load_dotenv()


# ==================================================================================
# SECTION 3: DATABASE URL (Where is the database?)
# ==================================================================================
#
# WHAT IS DATABASE_URL?
# =====================
# This is a connection string that tells SQLAlchemy where to find the database.
#
# FORMAT BREAKDOWN:
# sqlite:///./library.db
# └──┬──┘└─┬─┘└────┬─────┘
#    │     │       └── Database filename
#    │     └── Path (./ means current folder)
#    └── Database type (SQLite)
#
# WHAT IF THE .env FILE DOESN'T HAVE DATABASE_URL?
# ================================================
# os.getenv() takes a second parameter as default value.
# If DATABASE_URL isn't in .env, it uses "sqlite:///./library.db"
# This prevents crashes if someone forgets to set up .env
# ==================================================================================

# Get database URL from .env file, or use SQLite as fallback
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./library.db")


# ==================================================================================
# SECTION 4: CREATE ENGINE (The actual connection to database)
# ==================================================================================
#
# WHAT IS AN ENGINE?
# ==================
# The engine is the CORE of SQLAlchemy. It:
#   - Maintains the connection pool (multiple connections ready to use)
#   - Translates Python code into SQL
#   - Executes SQL statements on the database
#
# ANALOGY - Phone System:
# =======================
# Engine = The telephone exchange (connects calls)
# Session = One phone call (a conversation)
# Database = The person you're calling
#
# WHY THE SPECIAL connect_args?
# =============================
# SQLite normally only allows one thread to use the database at a time.
# FastAPI is ASYNCHRONOUS (handles multiple requests at once).
# "check_same_thread": False tells SQLite "it's OK to use from multiple threads"
# 
# IMPORTANT: This is ONLY for SQLite! Other databases (PostgreSQL, MySQL)
# don't need this parameter.
# ==================================================================================

# Create engine with special SQLite settings
engine = create_engine(
    DATABASE_URL,
    # Only add SQLite-specific argument if using SQLite
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)


# ==================================================================================
# SECTION 5: CREATE SESSIONMAKER (Factory for database conversations)
# ==================================================================================
#
# WHAT IS A SESSION?
# ==================
# A session is a CONVERSATION with the database.
# It represents a "unit of work" - a set of operations that should happen together.
#
# WHAT HAPPENS IN A SESSION?
# ==========================
# 1. You query data (SELECT)
# 2. You add new data (INSERT)
# 3. You update existing data (UPDATE)
# 4. You delete data (DELETE)
# 5. You COMMIT (save all changes) or ROLLBACK (undo all changes)
#
# WHY SessionLocal (capital S) vs session (lowercase s)?
# =======================================================
# - SessionLocal: A CLASS that creates session objects (like a cookie cutter)
# - session: An INSTANCE of a session (the actual cookie)
#
# ANALOGY:
# SessionLocal = A car factory (produces cars)
# session = One specific car (you drive it)
#
# WHAT DO autocommit=False AND autoflush=False MEAN?
# ==================================================
# - autocommit=False: Changes aren't saved until you call commit()
# - autoflush=False: Changes aren't sent to database until you call flush() or commit()
# 
# These give you CONTROL over when data is actually written to the database.
# ==================================================================================

# Create a session factory (can produce many session objects)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ==================================================================================
# SECTION 6: CREATE BASE CLASS (The foundation for all table classes)
# ==================================================================================
#
# WHAT IS Base?
# =============
# Base is a SPECIAL class that:
#   - Keeps track of ALL table classes you create
#   - Provides the metadata that SQLAlchemy uses to create tables
#   - Every table class must inherit from Base
#
# HOW DOES TABLE CREATION WORK?
# =============================
# 1. You define class BookDB(Base): (inherits from Base)
# 2. SQLAlchemy registers this class in Base.metadata
# 3. When you call Base.metadata.create_all(engine), SQLAlchemy:
#    - Looks at ALL registered classes
#    - Creates SQL CREATE TABLE statements
#    - Executes them on the database
#
# WHY DECLARATIVE BASE?
# =====================
# "Declarative" means you DECLARE what the table should look like,
# and SQLAlchemy figures out the SQL for you.
# ==================================================================================

# Base keeps track of all your table classes
Base = declarative_base()


# ==================================================================================
# SECTION 7: GET DATABASE SESSION DEPENDENCY
# ==================================================================================
#
# WHAT DOES get_db() DO?
# ======================
# This function is a FASTAPI DEPENDENCY.
# It creates a new database session for EACH request and closes it when done.
#
# WHY A GENERATOR (yield INSTEAD OF return)?
# ==========================================
# This is special FastAPI syntax for dependencies that need CLEANUP.
# 
# HOW YIELD WORKS:
# def get_db():
#     db = SessionLocal()      ← RUNS BEFORE endpoint (setup)
#     try:
#         yield db             ← GIVES db TO endpoint
#     finally:
#         db.close()           ← RUNS AFTER endpoint (cleanup)
#
# FLOW:
# 1. Request arrives
# 2. FastAPI runs get_db() until 'yield' → creates session
# 3. FastAPI runs your endpoint (with db parameter)
# 4. Your endpoint uses the database
# 5. Endpoint finishes
# 6. FastAPI returns to get_db() after 'yield' → closes session
#
# WHY CLOSE THE SESSION?
# ======================
# Database connections are LIMITED resources.
# If you don't close them, you'll eventually run out and the API will crash.
# get_db() ensures EVERY session is closed, even if an error occurs.
# ==================================================================================

def get_db():
    """
    DEPENDENCY: Provides a database session to endpoints.
    
    USAGE IN main.py:
        @app.get("/books")
        async def list_books(db: Session = Depends(get_db)):
            books = db.query(BookDB).all()
            return books
    
    HOW TO USE:
    - Add db: Session = Depends(get_db) to any endpoint that needs database access
    - Use db.query(), db.add(), db.commit(), etc.
    
    WHAT HAPPENS IF THERE'S AN ERROR?
    - The 'finally' block ALWAYS runs, even if an exception occurs
    - The session will ALWAYS be closed
    
    RELATIONSHIPS:
    - Called by: Any endpoint that needs database access
    - Returns: Session object (conversation with database)
    - Cleanup: Closes session after endpoint finishes
    """
    # Create a new session (start conversation with database)
    db = SessionLocal()
    
    try:
        # Give the session to the endpoint
        # The endpoint will use this to query/add/update/delete
        yield db
    finally:
        # AFTER the endpoint finishes, close the session
        # This frees up the database connection for other requests
        db.close()


# ==================================================================================
# SECTION 8: DATABASE MODELS (Table definitions)
# ==================================================================================
#
# WHAT IS A MODEL?
# ================
# A model is a Python class that represents a TABLE in the database.
# Each ATTRIBUTE (title, author, etc.) represents a COLUMN.
# Each INSTANCE of the class represents a ROW.
#
# EXAMPLE:
# BookDB table:
# | id | title          | author      | year | price |
# |----|----------------|-------------|------|-------|
# | 1  | Python Basics  | John Smith  | 2020 | 29.99 | ← One BookDB instance
# | 2  | FastAPI Mastery| Jane Doe    | 2023 | 39.99 | ← Another instance
#
# WHY TWO MODELS? (BookDB in database.py vs Book in main.py)
# ==========================================================
# - BookDB:   Database model (how data is STORED) - has id, all fields required
# - Book:     API model (how data is SENT/RECEIVED) - no id for creation
#
# SEPARATION OF CONCERNS:
# - database.py: Worries about storage (how data is saved)
# - main.py:     Worries about API (what users send/receive)
# ==================================================================================


# ==================================================================================
# MODEL 1: BookDB (Books table)
# ==================================================================================

class BookDB(Base):
    """
    WHAT: Represents the 'books' table in the database
    WHERE: Data is stored permanently in library.db
    WHEN: Used whenever we need to read/write books from database
    
    TABLE STRUCTURE:
    ┌─────────┬──────────────┬───────────┬──────┬────────┐
    │ id (PK) │ title        │ author    │ year │ price  │
    ├─────────┼──────────────┼───────────┼──────┼────────┤
    │ 1       │ Python Basics│ John Smith│ 2020 │ 29.99  │
    │ 2       │ FastAPI...   │ Jane Doe  │ 2023 │ 39.99  │
    └─────────┴──────────────┴───────────┴──────┴────────┘
    
    WHAT IS PK (Primary Key)?
    =========================
    - Every table should have a primary key
    - It UNIQUELY identifies each row
    - FastAPI uses it to find specific books (/books/42)
    - SQLite automatically increments it when you add new books
    
    WHAT IS index=True?
    ===================
    - Creates an "index" for faster searching
    - Like the index at the back of a book
    - Makes queries by that column much faster
    - We index 'id', 'username', 'email' (fields we search by often)
    
    WHAT IS nullable=False?
    =======================
    - Means the column cannot be empty (NULL)
    - Forces users to provide a value
    - Prevents incomplete data from being saved
    
    RELATIONSHIPS:
    - Used by: All book endpoints in main.py
    - Queried by: get_book_by_id(), list_books(), etc.
    - Modified by: create_book(), update_book(), delete_book()
    """
    
    # Name of the table in the database
    # This will appear as "books" when you inspect the database
    __tablename__ = "books"
    
    # id: Unique identifier for each book
    # primary_key=True: This is the main way to find a book
    # index=True: Create index for faster searching by ID
    id = Column(Integer, primary_key=True, index=True)
    
    # title: Book title
    # nullable=False: Cannot be empty
    title = Column(String, nullable=False)
    
    # author: Author name
    # nullable=False: Cannot be empty
    author = Column(String, nullable=False)
    
    # year: Publication year
    # nullable=False: Cannot be empty
    year = Column(Integer, nullable=False)
    
    # price: Book price (can have decimals like 29.99)
    # nullable=False: Cannot be empty
    price = Column(Float, nullable=False)


# ==================================================================================
# MODEL 2: UserDB (Users table)
# ==================================================================================

class UserDB(Base):
    """
    WHAT: Represents the 'users' table in the database
    WHERE: User accounts are stored permanently
    WHEN: Used during registration, login, and authentication
    
    TABLE STRUCTURE:
    ┌────┬──────────┬─────────────────┬─────────────────────┬───────────┐
    │ id │ username │ email           │ hashed_password     │ is_active │
    ├────┼──────────┼─────────────────┼─────────────────────┼───────────┤
    │ 1  │ moty     │ moty@email.com  │ $2b$12$KxQ...hash... │ 1         │
    │ 2  │ jane     │ jane@email.com  │ $2b$12$9fG...hash... │ 1         │
    └────┴──────────┴─────────────────┴─────────────────────┴───────────┘
    
    WHAT IS unique=True?
    ====================
    - Prevents duplicate values in this column
    - No two users can have the same username
    - No two users can have the same email
    - Database will reject attempts to insert duplicates
    
    WHY HASHED_PASSWORD?
    ====================
    - We NEVER store plain text passwords (huge security risk!)
    - If someone steals the database, they only see encrypted garbage
    - The hash cannot be reversed to get the original password
    
    HOW PASSWORD VERIFICATION WORKS:
    1. User enters password: "mysecret123"
    2. We hash it using bcrypt: "$2b$12$KxQ..."
    3. Compare with stored hash
    4. If they match → password is correct
    
    WHAT IS is_active?
    ==================
    - 1 = User can log in (active account)
    - 0 = User is banned/disabled (cannot log in)
    - Useful for admin features (disable bad users without deleting)
    
    RELATIONSHIPS:
    - Used by: Authentication endpoints in main.py
    - Queried by: authenticate_user(), get_current_user()
    - Modified by: register_user() (creates new users)
    - Future: Admin endpoints could update is_active to ban users
    """
    
    # Name of the table in the database
    __tablename__ = "users"
    
    # id: Unique identifier for each user
    # primary_key=True: Main way to identify a user
    # index=True: Faster lookups by ID
    id = Column(Integer, primary_key=True, index=True)
    
    # username: User's chosen username
    # unique=True: Cannot have two users with same username
    # nullable=False: Username is required
    # index=True: Faster searches by username (used in login!)
    username = Column(String, unique=True, nullable=False, index=True)
    
    # email: User's email address
    # unique=True: Cannot have two users with same email
    # nullable=False: Email is required
    # index=True: Faster searches by email
    email = Column(String, unique=True, nullable=False, index=True)
    
    # hashed_password: The ENCRYPTED password
    # nullable=False: Password is required
    # NOT unique: Multiple users can have same password hash (but that's fine)
    # NEVER store plain text passwords!
    hashed_password = Column(String, nullable=False)
    
    # is_active: Whether account is enabled
    # default=1: New users are active by default
    # 1 = active, 0 = disabled (banned)
    is_active = Column(Integer, default=1)


# ==================================================================================
# WHAT HAPPENS WHEN THIS FILE IS IMPORTED?
# ==================================================================================
#
# When main.py does "import database", this entire file runs.
# That means:
# 1. .env file is loaded
# 2. DATABASE_URL is read
# 3. Engine is created
# 4. SessionLocal is created
# 5. Base is created
# 6. BookDB and UserDB classes are defined
#
# BUT NOTE: The tables are NOT created here!
# Tables are created in main.py with:
#     database.Base.metadata.create_all(bind=engine)
#
# WHY CREATE TABLES IN main.py INSTEAD OF database.py?
# ====================================================
# - database.py: Defines WHAT tables should look like
# - main.py: Decides WHEN to create them (on startup)
# - Separates definition from execution
# ==================================================================================


# ==================================================================================
# QUICK REFERENCE: HOW TO USE THESE IN main.py
# ==================================================================================
#
# IMPORTING:
#   from database import SessionLocal, engine, get_db, BookDB, UserDB
#
# CREATING TABLES (in main.py after app = FastAPI()):
#   database.Base.metadata.create_all(bind=engine)
#
# GETTING A SESSION (in endpoints):
#   @app.get("/books")
#   def get_books(db: Session = Depends(get_db)):
#       books = db.query(BookDB).all()
#       return books
#
# QUERYING BOOKS:
#   # Get all books
#   all_books = db.query(BookDB).all()
#   
#   # Get one book by ID
#   book = db.query(BookDB).filter(BookDB.id == book_id).first()
#   
#   # Get books with filters
#   books = db.query(BookDB).filter(BookDB.author == "John").all()
#
# CREATING A BOOK:
#   new_book = BookDB(title="New Book", author="Moty", year=2024, price=29.99)
#   db.add(new_book)
#   db.commit()
#   db.refresh(new_book)  # Gets the auto-generated ID
#
# UPDATING A BOOK:
#   book.title = "Updated Title"
#   db.commit()
#
# DELETING A BOOK:
#   db.delete(book)
#   db.commit()
#
# USER OPERATIONS (similar to books):
#   # Find user by username
#   user = db.query(UserDB).filter(UserDB.username == username).first()
#   
#   # Create new user
#   new_user = UserDB(username="moty", email="m@e.com", hashed_password="hash", is_active=1)
#   db.add(new_user)
#   db.commit()
# ==================================================================================


# ==================================================================================
# TROUBLESHOOTING COMMON ERRORS
# ==================================================================================
#
# ERROR: "no such table: books"
# CAUSE: You haven't created the tables yet
# FIX: Run database.Base.metadata.create_all(bind=engine) in main.py
#
# ERROR: "UNIQUE constraint failed: users.username"
# CAUSE: Trying to register a username that already exists
# FIX: Check if username exists before inserting
#
# ERROR: "sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread"
# CAUSE: SQLite doesn't like multiple threads by default
# FIX: Make sure connect_args={"check_same_thread": False} is in create_engine()
#
# ERROR: "no such column: books.price"
# CAUSE: You changed the model but didn't update the database
# FIX: Delete library.db and restart (or use migrations with Alembic)
# ==================================================================================