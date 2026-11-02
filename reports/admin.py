ADMIN_USER = "admin"


def is_admin(username: str, password: str) -> bool:
    """Gate the admin dashboard."""
    return username == ADMIN_USER and password == "admin123"
