## CS490 Fitness App Backend

This README is for the frontend team.

Goal: make login and account creation easy to connect.

## Base URL

- Local backend: `http://127.0.0.1:8000`

## Auth Header (important)

All auth endpoints need a Bearer token from Auth0.

Use this header on every request:

```http
Authorization: Bearer YOUR_AUTH0_ACCESS_TOKEN
```

## Auth0 Wiring (Frontend + Backend)

Backend env vars must match your Auth0 setup:

- `AUTH0_DOMAIN` (example: `dev-abc123.us.auth0.com`)
- `AUTH0_API_AUDIENCE` (your Auth0 API Identifier)

Frontend Auth0 config must use the same values:

- `domain` = same as `AUTH0_DOMAIN`
- `authorizationParams.audience` = same as `AUTH0_API_AUDIENCE`

Simple frontend flow:

1. User logs in with Auth0.
2. Frontend gets access token (`getAccessTokenSilently`).
3. Frontend sends token in `Authorization: Bearer ...`.
4. Frontend calls backend endpoints (`/auth/login`, `/auth/me`, etc).

Minimal example:

```javascript
const token = await getAccessTokenSilently({
	authorizationParams: {
		audience: "YOUR_AUTH0_API_AUDIENCE"
	}
});

const res = await fetch("http://127.0.0.1:8000/auth/me", {
	headers: {
		Authorization: `Bearer ${token}`
	}
});
```

## Endpoints You Need

### 1) Login (safe to call every time)

- Method: `POST`
- URL: `/auth/login`
- What it does:
	- If user exists in DB, returns that user.
	- If user does not exist, creates user and returns it.

Example request:

```json
{
	"email": "sam@example.com",
	"first_name": "Sam",
	"last_name": "Lee",
	"profile_picture": "https://example.com/sam.jpg",
	"role": "client"
}
```

Example success response:

```json
{
	"user_id": 12,
	"auth0_sub": "auth0|abc123",
	"email": "sam@example.com",
	"first_name": "Sam",
	"last_name": "Lee",
	"role": "client",
	"is_new_user": false
}
```

### 2) Signup (optional explicit create)

- Method: `POST`
- URL: `/auth/signup`
- What it does:
	- Creates new account.
	- Returns `409` if account already exists.

Request body is the same as `/auth/login`.

### 3) Check Current User (connection check)

- Method: `GET`
- URL: `/auth/me`
- What it does:
	- Checks token + finds local user.
	- Use this when app starts to restore user session.

Example success response:

```json
{
	"user_id": 12,
	"auth0_sub": "auth0|abc123",
	"email": "sam@example.com",
	"first_name": "Sam",
	"last_name": "Lee",
	"role": "client",
	"is_new_user": false
}
```

### 4) Logout

- Method: `POST`
- URL: `/auth/logout`
- What it does:
	- Returns a simple message from backend.
	- Frontend still needs to clear token and call Auth0 logout.

### 5) RBAC quick checks (for frontend testing)

- Method: `GET`
- URLs:
	- `/auth/rbac/client`
	- `/auth/rbac/coach`
	- `/auth/rbac/admin`
- What they do:
	- Return `200` if the logged-in user has the required role.
	- Return `403` if user role is wrong.
	- Return `401` if token/user is invalid.


## Fetch Example (copy/paste)

```javascript
const token = "YOUR_AUTH0_ACCESS_TOKEN";

const res = await fetch("http://127.0.0.1:8000/auth/login", {
	method: "POST",
	headers: {
		"Content-Type": "application/json",
		Authorization: `Bearer ${token}`,
	},
	body: JSON.stringify({
		email: "sam@example.com",
		first_name: "Sam",
		last_name: "Lee",
		role: "client",
	}),
});

const data = await res.json();
console.log(data);
```

## Common Errors

- `401 Missing or invalid Authorization header`: token header is missing or malformed.
- `401 Token issuer mismatch` or `401 Token audience mismatch`: Auth0 settings/token config do not match backend config.
- `404 User not found in local database`: call `/auth/login` first.
- `409 Account already exists`: account was already created, use `/auth/login`.