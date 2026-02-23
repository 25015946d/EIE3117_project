# Lost and Found System (Vue + Django + MySQL)

This project implements an online lost-and-found system with:
- User registration/login/logout
- Create lost/found notices
- List all active notices
- Respond to notices
- Mark notices as completed
- View notice details with responses
- View notices created/responded by current user

## Project Structure

- `backend/` Django REST API
- `frontend/` Vue 3 app

## Backend Setup (Django)

### 1) Prerequisites
- Python 3.10+ installed
- MySQL running

### 2) Create database
```sql
CREATE DATABASE lost_found_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3) Configure environment
Copy and edit environment file:
```bash
cp backend/.env.example backend/.env
```
Set your MySQL password and secret key.

### 4) Install dependencies
```bash
# in backend/
python -m venv venv
# Windows PowerShell
.\\venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
```

### 5) Run migrations and start server
```bash
# in backend/
python manage.py makemigrations accounts notices
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Backend runs at: `http://localhost:8000`

## Frontend Setup (Vue)

### 1) Prerequisites
- Node.js 18+ and npm

### 2) Configure environment
```bash
cp frontend/.env.example frontend/.env
```

### 3) Install and run
```bash
# in frontend/
npm install
npm run serve
```

Frontend runs at: `http://localhost:8080`

## API Summary

- `POST /api/accounts/register/`
- `POST /api/accounts/login/`
- `POST /api/accounts/logout/`
- `GET /api/accounts/profile/`
- `PUT /api/accounts/profile/update/`
- `GET /api/notices/`
- `POST /api/notices/`
- `GET /api/notices/<id>/`
- `GET /api/notices/my-notices/`
- `POST /api/notices/<id>/respond/`
- `POST /api/notices/<id>/complete/`

## Notes

- Uploaded media is served in development via Django `MEDIA_URL`.
- Login state is persisted on the client and restored on page reload.
- If your PowerShell blocks activation scripts, run:
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  ```
.

testing 123