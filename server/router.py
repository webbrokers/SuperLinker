"""
Маршрутизация WSGI-запросов.
"""
from server import handlers


def dispatch(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/") or "/"

    # Статика
    if path.startswith("/static/"):
        return handlers.handle_static(environ, start_response)

    routes = {
        ("GET", "/"): handlers.handle_landing,
        ("GET", "/shorten"): handlers.handle_shorten_page,
        ("POST", "/api/shorten"): handlers.handle_api_shorten,
        ("GET", "/health"): handlers.handle_health,
        ("GET", "/admin/login"): handlers.handle_admin_login_get,
        ("POST", "/admin/login"): handlers.handle_admin_login_post,
        ("GET", "/admin/logout"): handlers.handle_admin_logout,
        ("GET", "/admin"): handlers.handle_admin_dashboard,
        ("GET", "/admin/links"): handlers.handle_admin_link_stats,
        ("GET", "/api/links/stats"): handlers.handle_api_link_stats,
        ("GET", "/api/links/clicks.csv"): handlers.handle_api_clicks_csv,
        ("GET", "/api/admin/export-all.csv"): handlers.handle_export_all_csv,
        ("POST", "/api/admin/generate-test-data"): handlers.handle_generate_test_data,
        ("POST", "/api/admin/clear-test-data"): handlers.handle_clear_test_data,
    }

    handler = routes.get((method, path))
    if handler:
        return handler(environ, start_response)

    # Редирект по slug: GET / HEAD /{slug}
    if method in ("GET", "HEAD") and path.count("/") == 1 and len(path) > 1:
        slug = path[1:]
        return handlers.handle_redirect(environ, start_response, slug)

    return handlers.handle_not_found(environ, start_response)
