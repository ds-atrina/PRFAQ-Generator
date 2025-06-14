from fastapi import  Depends, HTTPException, status
from fastapi.security import  HTTPBasic, HTTPBasicCredentials
import secrets, os

USERNAME = os.getenv("API_USERNAME", "")
PASSWORD = os.getenv("API_PASSWORD", "")

# --- Authentication ---
security = HTTPBasic()
def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, USERNAME)
    correct_password = secrets.compare_digest(credentials.password, PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
