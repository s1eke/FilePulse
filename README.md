# 📁 FilePulse

A modern, secure file sharing web application built with FastAPI and Python 3.13. FilePulse allows users to upload files, receive share codes, and download files with real-time progress tracking. All files automatically expire after 7 days.

## ✨ Features

- **Secure File Upload**: Drag-and-drop or click to upload files (up to 100MB)
- **Real-Time Progress**: Live upload/download progress with speed and ETA
- **Share Codes**: 8-character unique codes for easy file sharing
- **Automatic Expiry**: Files automatically deleted after 7 days
- **XSS Protection**: Comprehensive filename sanitization
- **Modern UI**: Glassmorphism design with dark mode
- **Mobile Responsive**: Optimized for all screen sizes
- **Background Cleanup**: Automatic scheduled deletion of expired files
- **RESTful API**: Well-documented FastAPI endpoints

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python 3.13)
- **Database**: SQLite with async support (aiosqlite)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Task Scheduling**: APScheduler
- **Security**: bleach for XSS prevention
- **Testing**: pytest with async support
- **Deployment**: Docker & Docker Compose

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd FilePulse
   ```

2. **Start with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

3. **Access the application**:
   - Open your browser and navigate to `http://localhost:8000`
   - API documentation (if enabled): `http://localhost:8000/docs`

4. **Stop the application**:
   ```bash
   docker-compose down
   ```

### Manual Installation

1. **Prerequisites**:
   - Python 3.13 or higher
   - pip

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

4. **Access the application** at `http://localhost:8000`

## ⚙️ Configuration

Environment variables can be set in a `.env` file or passed directly:

| Variable | Description | Default |
|----------|-------------|---------|
| `UPLOAD_DIR` | Directory for uploaded files | `./uploads` |
| `DATABASE_URL` | SQLite database connection URL | `sqlite+aiosqlite:///./filepulse.db` |
| `MAX_FILE_SIZE` | Maximum file size in bytes | `104857600` (100MB) |
| `ENABLE_DOCS` | Enable Swagger UI documentation | `false` |
| `FILE_EXPIRY_DAYS` | Days before files expire | `7` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |

**Example `.env` file**:
```env
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=104857600
ENABLE_DOCS=true
FILE_EXPIRY_DAYS=7
```

### Enabling API Documentation

By default, Swagger UI is **disabled** for security. To enable it:

**Docker**:
```bash
ENABLE_DOCS=true docker-compose up
```

**Manual**:
```bash
export ENABLE_DOCS=true
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then access documentation at `http://localhost:8000/docs`

## 📂 Project Structure

```
FilePulse/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database setup and session management
│   ├── models.py            # SQLAlchemy models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── upload.py        # Upload endpoints
│   │   └── download.py      # Download endpoints
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── security.py      # XSS protection, share code generation
│   │   └── scheduler.py     # Background file cleanup
│   └── static/
│       ├── index.html       # Upload page
│       ├── download.html    # Download page
│       ├── styles.css       # Global styles
│       ├── upload.js        # Upload functionality
│       └── download.js      # Download functionality
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Test fixtures
│   ├── test_upload.py       # Upload tests
│   ├── test_download.py     # Download tests
│   ├── test_security.py     # Security tests
│   └── test_scheduler.py    # Scheduler tests
├── Dockerfile               # Docker image definition
├── docker-compose.yml       # Docker Compose configuration
├── requirements.txt         # Python dependencies
├── .env.example            # Example environment variables
├── .gitignore
├── .dockerignore
└── README.md
```

## 🔒 Security Features

### XSS Protection

All filenames are sanitized to prevent cross-site scripting attacks:
- HTML tags removed
- Special characters escaped
- Path traversal attempts blocked
- SQL injection patterns filtered

### File Storage

- Files stored in date-based directory structure (`YYYY/MM/DD`)
- Unique timestamps prevent filename collisions
- Original filenames preserved for download

### Share Codes

- 8-character alphanumeric codes
- Cryptographically secure generation
- Unique constraint in database

## 🧪 Testing

Run the complete test suite:

```bash
# Install test dependencies (if not already installed)
pip install -r requirements.txt

# Run tests with coverage
pytest tests/ -v --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

Test coverage includes:
- ✅ File upload functionality
- ✅ File download functionality
- ✅ XSS and security protection
- ✅ Share code generation
- ✅ Expired file cleanup
- ✅ Database operations

## 📖 API Documentation

### Upload File

**POST** `/api/upload`

Upload a file and receive a share code.

**Request:**
- `Content-Type`: `multipart/form-data`
- `file`: File to upload (max 100MB)

**Response:**
```json
{
  "success": true,
  "share_code": "Abc123XY",
  "filename": "document.pdf",
  "file_size": 1024000,
  "upload_time": "2024-01-01T12:00:00",
  "expiry_time": "2024-01-08T12:00:00",
  "message": "File uploaded successfully. Share code: Abc123XY"
}
```

### Get File Info

**GET** `/api/file/{share_code}`

Retrieve file metadata.

**Response:**
```json
{
  "filename": "document.pdf",
  "file_size": 1024000,
  "upload_time": "2024-01-01T12:00:00",
  "expiry_time": "2024-01-08T12:00:00",
  "share_code": "Abc123XY"
}
```

### Download File

**GET** `/api/download/{share_code}`

Download file by share code.

**Response:**
- `Content-Type`: `application/octet-stream`
- `Content-Disposition`: `attachment; filename="document.pdf"`
- Stream of file bytes

### Health Check

**GET** `/health`

Check application health.

**Response:**
```json
{
  "status": "healthy",
  "service": "FilePulse"
}
```

## 🔄 Background Jobs

### File Cleanup Scheduler

FilePulse automatically runs a background job to clean up expired files:

- **Schedule**: Daily at 2:00 AM
- **Also runs**: On application startup
- **Action**: Deletes files and database records where `expiry_time < current_time`

## 🐳 Docker Deployment

### Build and Run

```bash
# Build and start
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Persistent Data

Docker Compose mounts two volumes for data persistence:
- `./uploads` - Uploaded files
- `./data` - SQLite database

These directories will be created automatically and persist across container restarts.

### Environment Variables in Docker

Set environment variables in `docker-compose.yml` or create a `.env` file:

```env
ENABLE_DOCS=true
MAX_FILE_SIZE=209715200
FILE_EXPIRY_DAYS=14
```

## 📱 Usage Guide

### Uploading Files

1. Visit the homepage at `http://localhost:8000`
2. Drag and drop a file or click to browse
3. Click "Upload File"
4. Watch real-time progress (speed, percentage, ETA)
5. Receive your unique 8-character share code
6. Copy the share link to share with others

### Downloading Files

1. Visit `http://localhost:8000/download.html` or use the shared link
2. Enter the share code
3. Click "Get File Info" to view file details
4. Click "Download File" to start download
5. Monitor real-time download progress

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Styled with modern CSS glassmorphism
- Tested with [pytest](https://pytest.org/)

---

**FilePulse** - Secure, Simple, Automatic File Sharing 🚀
