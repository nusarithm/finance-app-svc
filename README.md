# Finance Tracking App - Backend

Backend API untuk aplikasi finance tracking menggunakan FastAPI dan Supabase dengan arsitektur yang clean dan maintainable.

## 🚀 Features

- **Clean Architecture**: Organized code structure dengan separation of concerns
- **Authentication System**:
  - Register dengan validasi (name, username, phone, password)
  - Login dengan username dan password
  - Password di-hash menggunakan SHA256
  - JWT token untuk autentikasi
  - Protected endpoints dengan Bearer authentication
- **Validation**: Input validation dengan Pydantic
- **Error Handling**: Comprehensive error handling dan logging
- **Documentation**: Auto-generated API docs dengan FastAPI

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/                    # API route handlers
│   │   ├── __init__.py
│   │   └── auth.py            # Authentication endpoints
│   ├── core/                  # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py          # Application configuration
│   │   ├── database.py        # Database connection
│   │   ├── dependencies.py    # FastAPI dependencies
│   │   └── exceptions.py      # Exception handlers
│   ├── schemas/               # Pydantic schemas
│   │   ├── __init__.py
│   │   └── user.py           # User-related schemas
│   ├── services/              # Business logic
│   │   ├── __init__.py
│   │   └── auth_service.py    # Authentication service
│   ├── utils/                 # Utility functions
│   │   ├── __init__.py
│   │   └── security.py        # Security utilities
│   ├── __init__.py
│   └── main.py               # FastAPI app factory
├── main.py                    # Application entry point
├── requirements.txt
├── .env.example
├── database_schema.sql
└── README.md
```

## 🛠 Setup

### 1. Install Dependencies

```bash
# Create virtual environment (if not exists)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy file `.env.example` ke `.env`:

```bash
cp .env.example .env
```

Environment sudah dikonfigurasi dengan Supabase project Anda:
- Project ID: `quyqimhewbjyhqayuicn`
- Service Role Key: sudah terisi
- URL: `https://quyqimhewbjyhqayuicn.supabase.co`

### 3. Database Setup

Jalankan SQL script di `database_schema.sql` di Supabase SQL Editor untuk membuat tabel `users`.

### 4. Run Application

```bash
# Development mode
uvicorn main:app --reload

# Or using Python
python main.py
```

API akan tersedia di:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 API Endpoints

Base URL: `http://localhost:8000/api/v1`

### Authentication

#### 📝 Register User
- **POST** `/api/v1/auth/register`
- **Body**:
  ```json
  {
    "name": "John Doe",
    "username": "johndoe",
    "phone": "081234567890",
    "password": "password123"
  }
  ```

#### 🔐 Login User
- **POST** `/api/v1/auth/login`
- **Body**:
  ```json
  {
    "username": "johndoe",
    "password": "password123"
  }
  ```

#### 👤 Get Current User
- **GET** `/api/v1/auth/me`
- **Headers**: `Authorization: Bearer <access_token>`

#### ✏️ Update Current User
- **PUT** `/api/v1/auth/me`
- **Headers**: `Authorization: Bearer <access_token>`
- **Body**:
  ```json
  {
    "name": "John Updated",
    "phone": "081234567891"
  }
  ```

### Health Check

#### 💊 Health Status
- **GET** `/health`

## 🔒 Security Features

- **Password Hashing**: SHA256 untuk security
- **JWT Tokens**: Secure session management
- **Input Validation**: Comprehensive validation dengan Pydantic
- **Protected Routes**: Bearer token authentication
- **CORS**: Configurable Cross-Origin Resource Sharing
- **Error Handling**: Structured error responses

## 🏗 Architecture Patterns

- **Clean Architecture**: Separation of concerns
- **Service Layer**: Business logic isolation
- **Dependency Injection**: FastAPI dependencies
- **Schema Validation**: Pydantic models
- **Configuration Management**: Environment-based config
- **Exception Handling**: Centralized error handling

## 🧪 Development

### Code Structure Guidelines

1. **Controllers** (`app/api/`): Handle HTTP requests/responses
2. **Services** (`app/services/`): Business logic
3. **Schemas** (`app/schemas/`): Data validation
4. **Utils** (`app/utils/`): Helper functions
5. **Core** (`app/core/`): Application core (config, database, etc.)

### Adding New Features

1. Create schema in `app/schemas/`
2. Implement service in `app/services/`
3. Create API route in `app/api/`
4. Add route to `app/api/__init__.py`

### Environment Variables

```bash
# Application
APP_NAME=Finance Tracking API
DEBUG=false

# Supabase (already configured)
SUPABASE_URL=https://quyqimhewbjyhqayuicn.supabase.co
SUPABASE_PROJECT_ID=quyqimhewbjyhqayuicn

# JWT
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 🚀 Production Deployment

1. Set `DEBUG=false` in production
2. Use strong `SECRET_KEY`
3. Configure proper CORS origins
4. Set up proper logging
5. Use environment-specific configurations

## 🐳 Docker / Homelab Deployment

We provide a small, multi-stage Dockerfile plus a `docker-compose.yml` to run the app on your homelab.

Quick start (on your homelab or self-hosted runner):

```bash
# Build and run with compose
docker compose up -d --build

# Check logs
docker compose logs -f

# Stop
docker compose down
```

Notes:
- The app listens on container port `1234` and the compose file maps it to the same host port.
- Persistent uploads are stored in `./uploads` on the host and mounted into the container.
- The provided GitHub Actions workflow (`.github/workflows/deploy.yml`) will run on a `self-hosted` runner in your homelab and execute the same `docker compose up -d --build` on push to `main`.
- Ensure your self-hosted runner has Docker and Docker Compose installed and the runner user has permission to run Docker commands.

### Using Repository Secrets for Deployments

For automatic deployments we expect the following **Repository Secrets** to be set in GitHub (Settings → Secrets):

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_PROJECT_ID`
- `SECRET_KEY`
- `ALGORITHM` (optional, defaults to HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` (optional, defaults to 30)
- `ZAI_API_KEY`
- `UVICORN_WORKERS` (optional)

The workflow will map these secrets into the runner's environment and will fail early if critical secrets are missing.

Performance and image size tips:
- We use a multi-stage build that builds wheels in a builder stage and only installs runtime wheels in the final image to keep the final image smaller.
- Tune `UVICORN_WORKERS` (env var / compose file) according to your CPU count for best throughput.
- Use the `docker system prune -f` occasionally on the host to reclaim disk space.


## 📖 API Documentation

Kunjungi `/docs` untuk interactive API documentation dengan Swagger UI, atau `/redoc` untuk alternative documentation.