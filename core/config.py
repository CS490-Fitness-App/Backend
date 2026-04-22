# Loads environment variables (DB_URL, AUTH0_DOMAIN, AUTH0_API_AUDIENCE) into a typed Settings object.
# All other modules import from here instead of reading os.environ directly.

import os
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH, override=True)


class Settings:
	def __init__(self):
		# Auth0 (example: dev-abc123.us.auth0.com)
		self.auth0_domain = os.getenv("AUTH0_DOMAIN", "")
		self.auth0_api_audience = os.getenv("AUTH0_API_AUDIENCE", "")
		cors_allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "")
		self.cors_allowed_origins = [
			origin.strip()
			for origin in cors_allowed_origins.split(",")
			if origin.strip()
		]


settings = Settings()
