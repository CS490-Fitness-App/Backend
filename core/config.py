# Loads environment variables (DB_URL, AUTH0_DOMAIN, AUTH0_API_AUDIENCE) into a typed Settings object.
# All other modules import from here instead of reading os.environ directly.

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
	def __init__(self):
		# Auth0 (example: dev-abc123.us.auth0.com)
		self.auth0_domain = os.getenv("AUTH0_DOMAIN", "")
		self.auth0_api_audience = os.getenv("AUTH0_API_AUDIENCE", "")


settings = Settings()
