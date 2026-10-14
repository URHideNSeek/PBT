# Launch and hosting

## Windows
Download or clone the private repository using your GitHub account. Install Python 3.11+. From PowerShell in the repository folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

The process-only execution policy applies to this invocation. The script creates a virtual environment, installs dependencies and opens a local Streamlit server. Visit http://localhost:8501. Stop with Ctrl+C.

## macOS / Linux
```bash
bash run.sh
```

## Container on an existing private server
```bash
docker build -t trade-study .
docker run --rm -p 127.0.0.1:8501:8501 trade-study
```

The container runs as a non-root user. Host port binding is localhost only. For remote access, put it behind an authenticated HTTPS reverse proxy or private network. The app itself has no authentication. No public deployment has been performed. Container build requires Docker and has not been validated in the development runtime.

Session comparison data is temporary. Download scenario JSON to keep designs. Server restarts can discard session state. No engineering data is committed automatically.

Entry point: app.py. Dependency manifest: requirements.txt. Python: 3.11+. Runtime port: 8501. Health endpoint: /_stcore/health.
