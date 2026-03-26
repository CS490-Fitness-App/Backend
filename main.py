# Entry point for the Primal Fitness FastAPI application.
# Registers all routers, applies CORS middleware, and serves the uploads directory as static files.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers.auth import router as auth_router

app = FastAPI(title="Primal Fitness Backend")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(auth_router)

# serve everything inside the local ./uploads folder at the /uploads URL path
# e.g. ./uploads/profile_pics/abc.jpg becomes GET /uploads/profile_pics/abc.jpg
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
def health_check():
	return {"status": "ok", "service": "primal-fitness-backend"}
