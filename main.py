# Entry point for the Primal Fitness FastAPI application.
# Registers all routers, applies CORS middleware, and serves the uploads directory as static files.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 

# only import routers that have an actual APIRouter defined — stubs are excluded until implemented
# from routers import 

app = FastAPI(title="Primal Fitness API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# register each router; each one adds its own prefix (e.g. /exercises, /coaches, /users)


# serve everything inside the local ./uploads folder at the /uploads URL path
# e.g. ./uploads/profile_pics/abc.jpg becomes GET /uploads/profile_pics/abc.jpg
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
