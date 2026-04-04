# Entry point for the Primal Fitness FastAPI application.
# Registers all routers, applies CORS middleware, and serves the uploads directory as static files.

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers.admin import router as admin_router
from routers.auth import router as auth_router
from routers.chat import router as chat_router
from routers.payments import router as payments_router
from routers.clients import router as clients_router
from routers.coaches import router as coaches_router
from routers.dashboard import router as dashboard_router
from routers.exercises import router as exercises_router
from routers.workouts import router as workouts_router

app = FastAPI(title="Primal Fitness Backend")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(payments_router)
app.include_router(clients_router)
app.include_router(workouts_router)
app.include_router(coaches_router)
app.include_router(exercises_router)
app.include_router(dashboard_router)

# serve everything inside the local ./uploads folder at the /uploads URL path
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
def health_check():
	return {"status": "ok", "service": "primal-fitness-backend"}
