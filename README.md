# Lost and Found System (Vue + Django + MongoDB)

A modern, globally accessible lost and found platform built with Django REST API and Vue.js frontend, using MongoDB Atlas for cloud storage.

## 🚀 Features

- **User Management**: Secure registration/login/logout with JWT authentication
- **Notice Creation**: Create lost/found notices with image uploads
- **Global Access**: Cross-device accessibility with real-time updates
- **Response System**: Multiple users can respond to notices
- **Notice Lifecycle**: Mark notices as complete or delete them
- **Image Support**: Upload and display images for better identification
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## 🏗️ Technology Stack

### Backend (Django)
- **Framework**: Django 6.0.2 with Django REST Framework
- **Authentication**: JWT token-based authentication
- **Database**: Hybrid approach (MongoDB Atlas + SQLite)
- **File Storage**: MongoDB GridFS for images
- **API**: RESTful API with proper validation

### Frontend (Vue.js)
- **Framework**: Vue 3 with Composition API
- **State Management**: Vuex for authentication state
- **HTTP Client**: Axios for API communication
- **Styling**: Custom CSS with responsive design
- **Build Tool**: Vue CLI

### Database Architecture
- **MongoDB Atlas**: Cloud storage for notices and responses (global access)
- **SQLite**: Local storage for user authentication (security)
- **Hybrid Design**: Best of both worlds - scalability + security

## 📁 Project Structure

```
lost-and-found/
├── backend/                 # Django REST API
│   ├── accounts/           # User authentication
│   ├── notices/            # Notice and response models
│   ├── lost_found/         # Django project settings
│   └── requirements.txt    # Python dependencies
├── frontend/               # Vue.js application
│   ├── src/
│   │   ├── components/     # Vue components
│   │   ├── views/          # Page views
│   │   ├── store/          # Vuex store
│   │   └── main.js         # App entry point
│   └── package.json        # Node.js dependencies
└── README.md              # This file
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB Atlas account (free tier works)

### Backend Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd lost-and-found
```

2. **Create virtual environment**
```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure MongoDB Atlas**
- Create a free MongoDB Atlas account
- Create a cluster and database named `lost_found_db`
- Update the connection string in `backend/lost_found/settings.py`

5. **Run migrations and start server**
```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Backend runs at: `http://localhost:8000`

### Frontend Setup

1. **Install dependencies**
```bash
cd frontend
npm install
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env to set API base URL if needed
```

3. **Start development server**
```bash
npm run serve
```

Frontend runs at: `http://localhost:8081`

## 📡 API Endpoints

### Authentication
- `POST /auth/register/` - User registration
- `POST /auth/login/` - User login
- `POST /auth/logout/` - User logout
- `GET /auth/profile/` - Get current user profile

### Notices
- `GET /notices/` - List all notices
- `POST /notices/` - Create new notice (with image upload)
- `GET /notices/<id>/` - Get notice details
- `GET /notices/my-notices/` - Get current user's notices
- `POST /notices/<id>/respond/` - Respond to a notice
- `POST /notices/<id>/complete/` - Mark notice as complete
- `DELETE /notices/<id>/delete/` - Delete notice
- `GET /notices/image/<grid_id>/` - Serve uploaded images

## 🎯 Core Functions

### Notice Management
- ✅ Create notices with title, type, date, venue, contact, description
- ✅ Upload images for better item identification
- ✅ View all active notices globally
- ✅ Filter by notice type (Lost/Found)
- ✅ Mark notices as complete when items are found
- ✅ Delete notices (owners only)

### Response System
- ✅ Multiple users can respond to the same notice
- ✅ Real-time response display
- ✅ Prevents notice owners from responding to their own notices
- ✅ Shows responder information (nickname, email)

### User Features
- ✅ Secure JWT-based authentication
- ✅ User profiles with nicknames
- ✅ View own notices and responses
- ✅ Cross-device session persistence

### Global Features
- ✅ Real-time updates across all devices
- ✅ Image serving from cloud storage
- ✅ Responsive design for mobile and desktop
- ✅ Global accessibility through MongoDB Atlas

## 🔧 Configuration

### MongoDB Atlas Setup
1. Create free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a cluster (free tier is sufficient)
3. Create database user and whitelist IP addresses
4. Get connection string and update in `settings.py`

### Environment Variables
Backend configuration is handled in `backend/lost_found/settings.py`:
- MongoDB connection string
- CORS settings
- Media file handling

Frontend configuration in `frontend/.env`:
- `VUE_APP_API_BASE_URL` - Backend API URL

## 🚀 Deployment Notes

- **Development**: Uses Django development server and Vue CLI dev server
- **Production Ready**: Configured for MongoDB Atlas cloud deployment
- **Security**: JWT authentication with proper CORS configuration
- **Scalability**: MongoDB Atlas handles global traffic automatically

## 🐛 Troubleshooting

### Common Issues
- **MongoDB Connection**: Ensure IP is whitelisted in MongoDB Atlas
- **Image Upload**: Check MongoDB GridFS permissions
- **Authentication**: Verify JWT token configuration
- **CORS Errors**: Ensure frontend URL is allowed in Django settings

### PowerShell Issues
If PowerShell blocks activation scripts:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## 📄 License

This project is for educational purposes. Feel free to use and modify as needed.

---

**Built with ❤️ using Django, Vue.js, and MongoDB Atlas**