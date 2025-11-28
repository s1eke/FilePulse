# 📁 FilePulse

A modern, secure file sharing web application built with FastAPI and Python 3.13. FilePulse allows users to upload files, receive share codes, and download files with real-time progress tracking. All files automatically expire after 7 days.

## ✨ Features

- **Secure File Upload**: Drag-and-drop or click to upload files (up to 100MB by default)
- **Real-Time Progress**: Live upload/download progress with speed and ETA
- **Share Codes**: 8-character unique codes for easy file sharing
- **MD5 Deduplication**: Automatically detects and reuses duplicate files to save storage
- **Automatic Expiry**: Files automatically deleted after 7 days (or when last share expires)
- **XSS Protection**: Comprehensive filename sanitization
- **Modern UI**: Apple-style silver/white design with glassmorphism
- **Unified Interface**: Upload and download on the same page
- **Mobile Responsive**: Optimized for all screen sizes
- **Background Cleanup**: Automatic scheduled deletion of expired files
- **Flexible File Size Limits**: Support for MB/GB units (e.g., "100MB", "2GB")
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
| `MAX_FILE_SIZE` | Maximum file size (supports MB/GB units) | `100MB` |
| `ENABLE_DOCS` | Enable Swagger UI documentation | `false` |
| `FILE_EXPIRY_DAYS` | Days before files expire | `7` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |

**Example `.env` file**:
```env
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=500MB  # Supports: 100MB, 1GB, 2.5GB, etc.
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
│   ├── config.py            # Configuration with MB/GB unit support
│   ├── database.py          # Database setup and session management
│   ├── models.py            # SQLAlchemy models (FileRecord with MD5)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── upload.py        # Upload with MD5 deduplication
│   │   └── download.py      # Download endpoints
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── security.py      # XSS protection, share code generation
│   │   ├── file_utils.py    # MD5 calculation utilities
│   │   └── scheduler.py     # Background file cleanup with dedup support
│   └── static/
│       ├── index.html       # Unified upload/download page
│       ├── download.html    # Standalone download page
│       ├── styles.css       # Apple-style silver/white theme
│       ├── upload.js        # Upload functionality
│       ├── download.js      # Download functionality
│       └── download-inline.js  # Download for unified page
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

## 🗄️ Database Schema

### FileRecord Table

The `file_records` table stores metadata for all uploaded files:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT | Unique record ID |
| `filename` | VARCHAR(255) | NOT NULL | Stored filename (with timestamp and share code) |
| `original_filename` | VARCHAR(255) | NOT NULL | User's original filename (sanitized) |
| `share_code` | VARCHAR(8) | UNIQUE, NOT NULL, INDEXED | 8-character alphanumeric share code |
| `uploader_ip` | VARCHAR(45) | NOT NULL | IP address of uploader (supports IPv6) |
| `upload_time` | DATETIME | NOT NULL | UTC timestamp of upload |
| `expiry_time` | DATETIME | NOT NULL, INDEXED | Auto-calculated expiry (upload_time + 7 days) |
| `file_path` | VARCHAR(512) | NOT NULL | Physical file path on server |
| `file_size` | INTEGER | NOT NULL | File size in bytes |
| `file_md5` | VARCHAR(32) | NOT NULL, INDEXED | MD5 hash of file content |

**Indexes**:
- `idx_share_code`: On `share_code` (automatic via UNIQUE constraint)
- `idx_expiry_time`: On `expiry_time` for efficient cleanup queries
- `idx_file_md5`: On `file_md5` for duplicate detection

**MD5 Deduplication**:
- When a file is uploaded, its MD5 hash is calculated
- If a file with the same MD5 exists, the new share reuses the existing file path
- Multiple `FileRecord` entries can point to the same physical file
- The physical file is only deleted when ALL shares pointing to it have expired
- Each share has its own unique `share_code` and `expiry_time`

**Example Records**:

```sql
-- Two users upload the same file, creating two share codes but one physical file
INSERT INTO file_records VALUES (
  1, '1732800000000_Abc123XY_document.pdf', 'document.pdf', 'Abc123XY',
  '192.168.1.100', '2024-01-01 12:00:00', '2024-01-08 12:00:00',
  '/uploads/2024/01/01/1732800000000_Abc123XY_document.pdf', 1024000,
  '5d41402abc4b2a76b9719d911017c592'
);

INSERT INTO file_records VALUES (
  2, '1732800000000_Abc123XY_document.pdf', 'report.pdf', 'Def456ZW',
  '192.168.1.101', '2024-01-02 15:30:00', '2024-01-09 15:30:00',
  '/uploads/2024/01/01/1732800000000_Abc123XY_document.pdf', 1024000,
  '5d41402abc4b2a76b9719d911017c592'  -- Same MD5 hash
);
```

In this example, both shares reference the same physical file, but the file will only be deleted after 2024-01-09 15:30:00 (when the last share expires).

## 🔒 Security Features

### XSS Protection

All filenames are sanitized to prevent cross-site scripting attacks:
- HTML tags removed
- Dangerous characters filtered (< > : " / \ | ? *)
- Path traversal attempts blocked
- Control characters removed

### File Storage

- Files stored in date-based directory structure (`YYYY/MM/DD`)
- Unique timestamps prevent filename collisions
- Original filenames preserved for download
- **MD5 deduplication**: Duplicate files share the same physical storage

### MD5 Deduplication

- Each uploaded file's MD5 hash is calculated
- Files with identical content are stored only once
- Multiple share codes can reference the same physical file
- Storage-efficient: Same file uploaded 100 times = stored once
- Smart cleanup: Physical file deleted only when ALL shares expire

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
2. Ensure "Upload File" mode is selected
3. Drag and drop a file or click to browse
4. Click "Upload File"
5. Watch real-time progress (speed, percentage, ETA)
6. Receive your unique 8-character share code
7. Copy the share link to share with others

**Note**: If you upload a file that was previously uploaded (same content), FilePulse will automatically detect it using MD5 hash and reuse the existing file, saving storage space.

### Downloading Files

**Option 1: Using Share Link**
1. Open the shared link (e.g., `http://localhost:8000/download.html?code=Abc123XY`)
2. File info is displayed automatically
3. Click "Download File"
4. Monitor real-time download progress

**Option 2: On Homepage**
1. Visit `http://localhost:8000`
2. Click "Download File" button to switch modes
3. Enter the share code
4. Click "Get File Info" to view file details
5. Click "Download File" to start download
6. Monitor real-time download progress

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
