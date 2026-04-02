# ==================================================================================
# FILE: config.py
# ==================================================================================
#
# WHAT IS THIS FILE?
# ==================
# This file is the CENTRAL HUB for ALL your application settings.
# It reads secrets and configuration from the .env file and makes them
# available to the rest of your application in a clean, organized way.
#
# WHY DO WE NEED A SEPARATE CONFIG FILE?
# ======================================
# Without this file, you'd have to write os.getenv() everywhere:
#   - In main.py: SECRET_KEY = os.getenv("SECRET_KEY")
#   - In database.py: DATABASE_URL = os.getenv("DATABASE_URL")
#   - In middleware.py: DEBUG = os.getenv("DEBUG")
#
# Problems with that approach:
#   1. DUPLICATION: Same code in multiple files
#   2. HARD TO CHANGE: Update settings in many places
#   3. NO TYPE CHECKING: No IDE help, easy to make typos
#   4. NO DEFAULTS: Must handle missing values everywhere
#
# With config.py:
#   - ONE place to define ALL settings
#   - ONE place to change settings
#   - Type hints tell you what each setting should be
#   - Default values prevent crashes
#   - ALL files import from ONE source
#
# WHAT IS THE .env FILE?
# ======================
# The .env file is a SIMPLE TEXT FILE that stores key=value pairs.
# It is NOT committed to Git (secrets stay secret).
#
# Example .env file:
#   DATABASE_URL=sqlite:///./library.db
#   APP_NAME=My Library API
#   DEBUG=True
#   SECRET_KEY=your-super-secret-key-here
#   API_VERSION=1.0.0
#
# WHY NOT PUT THESE DIRECTLY IN CODE?
# ===================================
# 1. SECURITY: If you push code to GitHub, secrets become public!
# 2. ENVIRONMENTS: Development, testing, and production need different settings
# 3. FLEXIBILITY: Change settings without changing code
# 4. TEAM WORK: Different developers can have different .env files
#
# WHAT IS THE Settings CLASS?
# ===========================
# The Settings class is a CONTAINER that holds ALL configuration values.
# Each attribute (DATABASE_URL, APP_NAME, etc.) is one setting.
#
# BENEFITS OF USING A CLASS:
# - Organization: All settings in one place
# - Type hints: IDE knows DATABASE_URL is a string, DEBUG is a boolean
# - Default values: settings.DEBUG defaults to False if not in .env
# - Single instance: settings = Settings() creates ONE object everyone uses
#
# RELATIONSHIPS:
# ==============
# - .env file:     Provides the raw key=value pairs
# - python-dotenv: Reads the .env file (imported here)
# - os.getenv():   Gets values from environment
# - Settings class: Organizes values into typed attributes
# - settings object: Single instance exported for other files to import
#
# FILES THAT USE config.py:
# =========================
# - main.py:        Uses settings.APP_NAME, settings.DEBUG, settings.SECRET_KEY
# - database.py:    Uses settings.DATABASE_URL
# - (Any future file): Can import settings for configuration
# ==================================================================================


# ==================================================================================
# SECTION 1: IMPORTS
# ==================================================================================
#
# WHAT IS 'os'?
# =============
# 'os' is Python's OPERATING SYSTEM interface module.
# It provides functions for interacting with the environment.
# os.getenv() reads environment variables (including those from .env file)
#
# WHAT IS 'dotenv'?
# =================
# python-dotenv is a library that LOADS .env file into environment variables.
# Without it, os.getenv() would only see system environment variables,
# not the ones you put in your .env file.
#
# WHY DO WE NEED BOTH?
# ====================
# 1. load_dotenv(): Reads .env file and puts variables into environment
# 2. os.getenv():   Reads variables from environment (both system AND .env)
#
# ANALOGY - Mail Delivery:
# ========================
# .env file = Letters in your mailbox
# load_dotenv() = Mail carrier bringing letters inside your house
# os.getenv() = You opening a letter to read what's inside
# ==================================================================================

import os
from dotenv import load_dotenv


# ==================================================================================
# SECTION 2: LOAD .env FILE
# ==================================================================================
#
# WHAT DOES load_dotenv() DO EXACTLY?
# ===================================
# When you call load_dotenv(), it:
#   1. Looks for a file named '.env' in the current directory
#   2. Reads every line like "KEY=VALUE"
#   3. Adds each KEY as an environment variable with VALUE
#
# EXAMPLE:
# .env file contains:
#   DATABASE_URL=sqlite:///./library.db
#   SECRET_KEY=abc123
#
# After load_dotenv():
#   os.getenv("DATABASE_URL") returns "sqlite:///./library.db"
#   os.getenv("SECRET_KEY") returns "abc123"
#
# WHY CALL THIS FIRST?
# ====================
# The Settings class uses os.getenv() to read values.
# If we don't call load_dotenv() FIRST, os.getenv() won't see the .env file!
# Order matters:
#   1. load_dotenv()  ← Reads .env into environment
#   2. class Settings ← Now os.getenv() can find the values
#
# WHAT IF THERE'S NO .env FILE?
# =============================
# load_dotenv() simply does nothing (no error).
# os.getenv() will return None for missing keys.
# That's why we provide DEFAULT values as second parameter.
# ==================================================================================

# Load all variables from .env file into environment variables
# This MUST be called before any os.getenv() calls!
load_dotenv()


# ==================================================================================
# SECTION 3: SETTINGS CLASS (The Configuration Container)
# ==================================================================================
#
# WHAT IS A CLASS?
# ================
# A class is a BLUEPRINT for creating objects.
# Think of it like a cookie cutter:
#   - Class = Cookie cutter (the shape)
#   - Object = Actual cookie (one specific instance)
#
# WHY USE A CLASS FOR SETTINGS?
# =============================
# Without a class:
#   DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./library.db")
#   APP_NAME = os.getenv("APP_NAME", "FastAPI Library")
#   DEBUG = os.getenv("DEBUG", "False") == "true"
#   (variables just floating around - messy)
#
# With a class:
#   settings = Settings()
#   settings.DATABASE_URL  ← Clean, organized, IDE autocomplete works!
#
# WHAT IS THE BENEFIT OF Type Hints (: str, : bool)?
# ==================================================
# Type hints tell you (and your IDE) what type each setting should be:
#   DATABASE_URL: str   ← This should be text
#   DEBUG: bool         ← This should be True/False
#
# This helps PREVENT BUGS:
#   if settings.DEBUG:  ← IDE knows DEBUG is boolean, gives proper highlighting
#   db_url = settings.DATABASE_URL  ← IDE knows this is a string
#
# WHAT IS THE 'settings' OBJECT AT THE BOTTOM?
# ============================================
# settings = Settings() creates ONE instance of the Settings class.
# This is called a SINGLETON - a single object that everyone shares.
#
# WHY CREATE ONE INSTANCE?
# ========================
# - Consistency: Everyone gets the SAME values
# - Performance: Settings are loaded ONCE, not every time
# - Simplicity: Just `from config import settings` in any file
# ==================================================================================

class Settings:
    """
    All configuration settings for the FastAPI Library application.
    
    This class centralizes ALL configuration values from:
    - .env file (secrets, database URL, etc.)
    - Default values (fallbacks if .env missing)
    
    HOW TO USE IN OTHER FILES:
        from config import settings
        
        print(settings.APP_NAME)      # "My Library API"
        print(settings.DEBUG)         # True or False
        db_url = settings.DATABASE_URL
        
    WHY USE A CLASS INSTEAD OF GLOBAL VARIABLES?
        - Organization: All settings in one place
        - Type safety: IDE knows what type each setting is
        - Easy to add new settings: Just add a new attribute
        - Can add validation logic later if needed
    
    RELATED TO:
        - .env file: Provides raw values
        - main.py: Uses these settings
        - database.py: Uses DATABASE_URL
    """
    
    # ==========================================================================
    # DATABASE SETTINGS
    # ==========================================================================
    # WHERE: Where is your database?
    # WHY: Different environments (dev, test, prod) use different databases
    # DEFAULT: SQLite file in current folder (if not in .env)
    # TYPE: String (text)
    #
    # WHAT IS os.getenv("DATABASE_URL", "sqlite:///./library.db")?
    # ===========================================================
    # - First parameter "DATABASE_URL": Look for this key in environment
    # - Second parameter "sqlite:///./library.db": DEFAULT if not found
    #
    # So this line means:
    #   "Try to get DATABASE_URL from .env file.
    #    If it's not there, use SQLite database called library.db"
    # ==========================================================================
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./library.db")
    
    # ==========================================================================
    # APPLICATION SETTINGS
    # ==========================================================================
    # APP_NAME: The name of your API (appears on homepage)
    # DEFAULT: "FastAPI Library" (if not in .env)
    # TYPE: String
    # ==========================================================================
    APP_NAME: str = os.getenv("APP_NAME", "FastAPI Library")
    
    # ==========================================================================
    # DEBUG MODE
    # ==========================================================================
    # WHAT IS DEBUG MODE?
    # - True:  Show detailed error messages (useful for development)
    # - False: Hide error details (security for production)
    #
    # WHY THE COMPLEX CONVERSION?
    # ===========================
    # .env file stores EVERYTHING as strings:
    #   DEBUG=True  ← This is the STRING "True", not the boolean True
    #
    # We need to convert "True" → True and "False" → False
    # 
    # HOW THE CONVERSION WORKS:
    #   1. os.getenv("DEBUG", "False") → Gets "True" or "False" string
    #   2. .lower() → Makes lowercase ("true" or "false")
    #   3. == "true" → Compares to "true" string
    #   4. Result is actual boolean True or False
    #
    # EXAMPLE:
    #   If .env has DEBUG=True:
    #     os.getenv() returns "True"
    #     "True".lower() becomes "true"
    #     "true" == "true" → True (boolean)
    #
    #   If .env has DEBUG=False:
    #     "False".lower() becomes "false"
    #     "false" == "true" → False (boolean)
    #
    #   If .env has no DEBUG:
    #     Default "False" → False (boolean)
    # ==========================================================================
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # ==========================================================================
    # API VERSION
    # ==========================================================================
    # WHAT: Version number of your API (appears on homepage)
    # WHY: Helps clients know which version they're using
    # DEFAULT: "1.0.0"
    # TYPE: String
    # ==========================================================================
    API_VERSION: str = os.getenv("API_VERSION", "1.0.0")
    
    # ==========================================================================
    # SECURITY SETTINGS
    # ==========================================================================
    # WHAT IS SECRET_KEY?
    # ===================
    # The secret key is used to SIGN JWT tokens.
    # Think of it like a special stamp that only the server has.
    #
    # WHY IS IT SECRET?
    # =================
    # If someone steals your secret key, they can FORGE tokens!
    # They could create fake "admin" tokens and hack your API.
    #
    # WHY A DEFAULT VALUE?
    # ====================
    # The default "change-this-in-production" is a PLACEHOLDER.
    # It ensures the app runs even if you forget to set SECRET_KEY in .env.
    # But in PRODUCTION, you MUST change it to a strong random string!
    #
    # HOW TO GENERATE A STRONG SECRET KEY:
    #   python -c "import secrets; print(secrets.token_urlsafe(32))"
    #   Output example: "xK9mP2nQ5rT8vW1yZ4aB7cD0eF3gH6jL9oM2pR5sU8x"
    #
    # WHAT MAKES A GOOD SECRET KEY?
    # ============================
    # - Long (at least 32 characters)
    # - Random (not a word or phrase)
    # - Contains letters, numbers, and symbols
    # - Different for each environment (dev vs production)
    # ==========================================================================
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production")


# ==================================================================================
# SECTION 4: CREATE SINGLETON INSTANCE
# ==================================================================================
#
# WHAT IS settings = Settings()?
# ==============================
# This creates ONE instance of the Settings class.
# 
# WHY CREATE IT HERE INSTEAD OF IN main.py?
# =========================================
# By creating it here, ANY file can import it:
#   from config import settings
#
# If we created it in main.py, other files couldn't access it easily.
#
# WHAT IS A SINGLETON?
# ====================
# A singleton is a design pattern where you create ONLY ONE instance of a class.
# Everyone shares the SAME instance with the SAME values.
#
# WHY SINGLETON FOR SETTINGS?
# ===========================
# - Consistency: Every file sees the same configuration
# - Efficiency: Settings are loaded once, not every time
# - Simplicity: Just import settings anywhere
#
# HOW OTHER FILES USE THIS:
# =========================
# In main.py:
#   from config import settings
#   print(settings.APP_NAME)  # "My Library API"
#
# In database.py:
#   from config import settings
#   DATABASE_URL = settings.DATABASE_URL
#
# In any new file:
#   from config import settings
#   if settings.DEBUG:
#       print("Debug mode is ON")
# ==================================================================================

# Create a single instance of Settings that everyone will use
# This instance loads values from .env ONCE when the app starts
settings = Settings()


# ==================================================================================
# SECTION 5: HOW SETTINGS FLOW THROUGH YOUR APPLICATION
# ==================================================================================
#
# COMPLETE DATA FLOW:
# ===================
#
# 1. YOU CREATE .env FILE:
#    DATABASE_URL=sqlite:///./library.db
#    APP_NAME=My Library API
#    DEBUG=True
#    SECRET_KEY=my-secret-key
#    API_VERSION=1.0.0
#
# 2. config.py LOADS .env:
#    load_dotenv() reads the file
#    os.getenv() gets each value
#    Settings class organizes them
#    settings = Settings() creates the object
#
# 3. OTHER FILES IMPORT settings:
#    from config import settings
#
# 4. OTHER FILES USE settings:
#    database.py: uses settings.DATABASE_URL
#    main.py: uses settings.APP_NAME, settings.DEBUG, settings.SECRET_KEY
#
# VISUAL REPRESENTATION:
# =====================
# 
#   .env file                    config.py                      main.py
#   ┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
#   │DATABASE_URL=... │─────────▶│ load_dotenv()   │          │ from config     │
#   │APP_NAME=My API  │          │ os.getenv()     │          │ import settings │
#   │DEBUG=True       │          │ Settings class  │          │                 │
#   │SECRET_KEY=...   │          │ settings = ...  │─────────▶│ settings.APP_NAME│
#   └─────────────────┘          └─────────────────┘          └─────────────────┘
#                                                                        │
#                                                                        ▼
#                                                              ┌─────────────────┐
#                                                              │ "My Library API"│
#                                                              └─────────────────┘
#
# WHY THIS IS BETTER THAN HARDCODING:
# ===================================
# HARDCODING (BAD):
#   DATABASE_URL = "sqlite:///./library.db"  ← In database.py
#   APP_NAME = "My Library API"              ← In main.py
#   SECRET_KEY = "my-secret-key"             ← In main.py
#
# Problems:
#   - To change database, edit database.py (code change!)
#   - Secret key visible in code (security risk!)
#   - Different environments? Copy entire files!
#
# WITH config.py (GOOD):
#   - Change .env file, restart server (no code change!)
#   - Secret key in .env (not in code!)
#   - Different environments = different .env files
# ==================================================================================


# ==================================================================================
# SECTION 6: COMMON QUESTIONS AND ANSWERS
# ==================================================================================
#
# Q: WHAT HAPPENS IF I FORGET TO CREATE .env FILE?
# A: The app still works! Default values will be used:
#    - DATABASE_URL → "sqlite:///./library.db"
#    - APP_NAME → "FastAPI Library"
#    - DEBUG → False
#    - SECRET_KEY → "change-this-in-production"
#
# Q: WHY DOES DEBUG DEFAULT TO False?
# A: Security! Production should NEVER show debug errors to users.
#    Developers should explicitly set DEBUG=True in .env.
#
# Q: CAN I ADD MORE SETTINGS?
# A: YES! Just add new lines to .env and new attributes to Settings class:
#    
#    In .env:
#        MAX_BOOKS_PER_PAGE=20
#    
#    In config.py (inside Settings class):
#        MAX_BOOKS_PER_PAGE: int = int(os.getenv("MAX_BOOKS_PER_PAGE", "10"))
#
# Q: WHY DO I NEED TO CONVERT TYPES (like int(), bool())?
# A: os.getenv() ALWAYS returns strings. If you need a number, convert it:
#    MAX_BOOKS_PER_PAGE: int = int(os.getenv("MAX_BOOKS_PER_PAGE", "10"))
#
# Q: WHAT IF I NEED TO USE settings IN database.py?
# A: Just import it:
#    from config import settings
#    DATABASE_URL = settings.DATABASE_URL
#
# Q: CAN I CHANGE SETTINGS WHILE THE SERVER IS RUNNING?
# A: No. Changes to .env require server restart.
#    uvicorn --reload will auto-restart when you save .env!
#
# Q: IS .env FILE SAFE TO COMMIT TO GIT?
# A: NO! NEVER commit .env to Git! Add it to .gitignore:
#    echo .env >> .gitignore
#
# Q: WHAT IF DIFFERENT DEVELOPERS NEED DIFFERENT SETTINGS?
# A: Each developer has their OWN .env file (not shared via Git)
#    - Developer A: DATABASE_URL=sqlite:///./dev_a.db
#    - Developer B: DATABASE_URL=sqlite:///./dev_b.db
# ==================================================================================


# ==================================================================================
# SECTION 7: TROUBLESHOOTING
# ==================================================================================
#
# PROBLEM: settings.DATABASE_URL is None
# CAUSE: .env file not found or DATABASE_URL not in it
# FIX: 
#   1. Check if .env exists in the same folder as config.py
#   2. Check if .env has DATABASE_URL= line
#   3. Check for typos (DATABASE_URL not DATABASE-URL)
#
# PROBLEM: settings.DEBUG is False but .env has DEBUG=True
# CAUSE: 
#   - .env might have DEBUG = True (spaces around =)
#   - .env might have DEBUG="True" (quotes)
#   - Case sensitivity: DEBUG=true vs DEBUG=True
# FIX: Use exact format: KEY=VALUE (no spaces, no quotes)
#
# PROBLEM: settings.SECRET_KEY has default value even though .env has SECRET_KEY
# CAUSE: SECRET_KEY in .env might have spaces or quotes
# FIX: .env should have: SECRET_KEY=actual-key-here (no spaces, no quotes)
#
# PROBLEM: Import error "cannot import name 'settings' from 'config'"
# CAUSE: Circular import (config imports something that imports config)
# FIX: Make sure config.py doesn't import from files that import config
# ==================================================================================