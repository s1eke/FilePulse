# 📁 FilePulse

A secure, simple file sharing application. Upload files, get a 6-digit code, and share. Files expire automatically after 7 days.

## ✨ Features

- **Simple Sharing**: Upload and get a 6-character code.
- **Auto Expiry**: Files are deleted after 7 days.
- **Secure**: XSS protection and file sanitization.
- **Efficient**: MD5 deduplication saves storage space.
- **Modern UI**: Clean, Apple-style interface.

## 🎯 Planned Features

- **Frontend MD5 Calculation**: Calculate file MD5 on client side to avoid duplicate uploads and reduce server traffic.

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
git clone <repository-url>
cd FilePulse
docker-compose up -d
```

Visit `http://localhost:8000` to start sharing.

### Manual Setup

1.  Install dependencies: `pip install -r requirements.txt`
2.  Run server: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## ⚙️ Configuration

Set these in `.env` or `docker-compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_FILE_SIZE` | `100MB` | Max upload size (e.g., `500MB`, `1GB`) |
| `FILE_EXPIRY_DAYS` | `7` | Days to keep files |
| `UPLOAD_DIR` | `./uploads` | Storage directory |

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.13)
- **Frontend**: Vanilla HTML/JS (Jinja2)
- **Database**: SQLite (Async)
- **Task Queue**: APScheduler


## 📄 License

MIT License.
