# /root/api/routers/filesystem.py
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pathlib import Path
import secrets

router = APIRouter(prefix="/fs", tags=["filesystem"])
security = HTTPBasic()

# Configure your basic-auth credentials here (or load from env)
VALID_USERNAME = "admin"
VALID_PASSWORD = "supersecret"

BASE_DIR = Path("/root/api").resolve()

def get_current_user(creds: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(creds.username, VALID_USERNAME)
    correct_password = secrets.compare_digest(creds.password, VALID_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return creds.username

@router.get("/list")
def list_dir(path: str = "/", username: str = Depends(get_current_user)):
    target = (BASE_DIR / path.lstrip("/")).resolve()
    if BASE_DIR not in target.parents and target != BASE_DIR:
        raise HTTPException(400, "Path outside allowed directory")
    if not target.exists() or not target.is_dir():
        raise HTTPException(404, "Directory not found")
    entries = []
    for child in sorted(target.iterdir()):
        entries.append({
            "name": child.name + ("/" if child.is_dir() else ""),
            "type": "directory" if child.is_dir() else "file"
        })
    return {"entries": entries}

@router.get("/read")
def read_file(path: str, username: str = Depends(get_current_user)):
    target = (BASE_DIR / path.lstrip("/")).resolve()
    if BASE_DIR not in target.parents and target != BASE_DIR:
        raise HTTPException(400, "Path outside allowed directory")
    if not target.exists() or not target.is_file():
        raise HTTPException(404, "File not found")
    try:
        return target.read_text(encoding="utf-8")
    except Exception as e:
        raise HTTPException(500, f"Error reading file: {e}")
