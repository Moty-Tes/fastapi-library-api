# 📚 Library API

A REST API for managing books with user authentication.

## 🚀 Features

- Create, read, update, delete books
- User registration and login
- JWT authentication
- Automatic API documentation

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/books` | List all books |
| GET | `/books/{id}` | Get one book |
| POST | `/books` | Create a book |
| PUT | `/books/{id}` | Update a book |
| PATCH | `/books/{id}` | Partial update |
| DELETE | `/books/{id}` | Delete a book |
| POST | `/users/register` | Register new user |
| POST | `/users/login` | Login |
| GET | `/users/me` | Get current user |

## 🛠️ Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/fastapi-library-api.git

# 2. Enter the directory
cd fastapi-library-api

# 3. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file
echo DATABASE_URL=sqlite:///./library.db > .env
echo SECRET_KEY=your-secret-key >> .env

# 6. Run the server
uvicorn main:app --reload