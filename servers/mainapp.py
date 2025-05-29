from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import APIRouter
import secrets, os

app = FastAPI(title="PRFAQ Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Authentication ---
security = HTTPBasic()
USERNAME = os.getenv("API_USERNAME", "")
PASSWORD = os.getenv("API_PASSWORD", "")

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

# Central router with version prefix
api_router = APIRouter(prefix="/api/v1")

# Register use case routers with sub-prefixes
from api.prfaq_api import router as prfaq_router

api_router.include_router(prfaq_router, prefix="/prfaq")

# Register main API router with app
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8082))
    uvicorn.run("mainapp:app", host="0.0.0.0", port=port, reload=True)