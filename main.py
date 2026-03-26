# Entry point for the Primal Fitness FastAPI application.
# Registers all routers, applies CORS middleware, and serves the uploads directory as static files.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/")
def health_check():
	return {"status": "ok", "service": "primal-fitness-backend"}
