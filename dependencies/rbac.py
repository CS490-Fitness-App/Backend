# Provides role-based access control dependencies: get_current_user, require_client, require_coach, require_admin.
# Each dependency resolves the authenticated user from the database and enforces their role, raising 401/403 as needed.
