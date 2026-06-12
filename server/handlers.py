"""
Обработчики HTTP-маршрутов SuperLinker.
"""
import html
import json

import config
from server import auth
from server.utils import (
    csv_response,
    get_client_ip,
    html_response,
    is_valid_url,
    json_response,
    parse_expires_days,
    parse_form,
    parse_query,
    redirect_response,
    render_template,
    static_file_response,
)
from services import links, rate_limit, stats, test_data


def _respond(start_response, result, extra_headers=None):
    status, headers, body = result
    if extra_headers:
        headers = list(headers) + list(extra_headers.items())
    start_response(status, headers)
    return [body]


def _require_admin(environ, start_response):
    if not auth.is_admin(environ):
        return redirect_response("/admin/login")
    return None


def _nav_context(active: str) -> dict:
    return {
        "nav_home": "active" if active == "home" else "",
        "nav_shorten": "active" if active == "shorten" else "",
        "nav_admin": "active" if active == "admin" else "",
        "base_url": config.BASE_URL,
    }


def handle_static(environ, start_response):
    path = environ.get("PATH_INFO", "")
    result = static_file_response(path)
    if result is None:
        return _respond(start_response, html_response(
            render_template("404.html", message="Страница не найдена", **_nav_context("")),
            "404 Not Found",
        ))
    return _respond(start_response, result)


def handle_not_found(environ, start_response):
    return _respond(start_response, html_response(
        render_template("404.html", message="Страница не найдена", **_nav_context("")),
        "404 Not Found",
    ))


def handle_health(environ, start_response):
    return _respond(start_response, json_response({"status": "ok"}))


def handle_landing(environ, start_response):
    body = render_template("landing.html", **_nav_context("home"))
    return _respond(start_response, html_response(body))


def handle_shorten_page(environ, start_response):
    ok, remaining = rate_limit.check_rate_limit(get_client_ip(environ))
    body = render_template(
        "shorten.html",
        rate_remaining=str(remaining),
        rate_limit=str(config.RATE_LIMIT_PER_DAY),
        error="",
        **_nav_context("shorten"),
    )
    return _respond(start_response, html_response(body))


def handle_api_shorten(environ, start_response):
    ip = get_client_ip(environ)
    ok, remaining = rate_limit.check_rate_limit(ip)
    if not ok:
        return _respond(start_response, json_response(
            {"error": f"Лимит: {config.RATE_LIMIT_PER_DAY} ссылок в день с вашего IP"},
            "429 Too Many Requests",
        ))

    data = parse_form(environ)
    url = data.get("url", "")
    valid, err = is_valid_url(url)
    if not valid:
        return _respond(start_response, json_response({"error": err}, "400 Bad Request"))

    custom_slug = data.get("slug", "").strip() or None
    expires_at = parse_expires_days(data.get("expires_days", ""))
    utm_source = data.get("utm_source", "").strip() or None
    utm_medium = data.get("utm_medium", "").strip() or None
    utm_campaign = data.get("utm_campaign", "").strip() or None

    try:
        link = links.create_link(
            original_url=url,
            custom_slug=custom_slug,
            expires_at=expires_at,
            utm_source=utm_source,
            utm_medium=utm_medium,
            utm_campaign=utm_campaign,
        )
    except ValueError as e:
        return _respond(start_response, json_response({"error": str(e)}, "400 Bad Request"))

    rate_limit.increment_rate_limit(ip)
    _, new_remaining = rate_limit.check_rate_limit(ip)
    link["remaining_today"] = new_remaining
    return _respond(start_response, json_response(link))


def handle_redirect(environ, start_response, slug: str):
    link = links.get_link_by_slug(slug)
    if not link:
        return _respond(start_response, html_response(
            render_template("404.html", message="Ссылка не найдена", **_nav_context("")),
            "404 Not Found",
        ))

    if links.is_link_expired(link):
        return _respond(start_response, html_response(
            render_template("expired.html", **_nav_context("")),
            "410 Gone",
        ))

    # HEAD — только статус редиректа, без записи клика
    if environ.get("REQUEST_METHOD", "GET").upper() == "HEAD":
        target = links.build_redirect_url(link)
        return _respond(start_response, redirect_response(target))

    ip = get_client_ip(environ)
    ua = environ.get("HTTP_USER_AGENT", "")
    referer = environ.get("HTTP_REFERER", "")
    stats.record_click(link["id"], ip, ua, referer)

    target = links.build_redirect_url(link)
    return _respond(start_response, redirect_response(target))


def handle_admin_login_get(environ, start_response):
    if auth.is_admin(environ):
        return _respond(start_response, redirect_response("/admin"))
    body = render_template("admin_login.html", error="", **_nav_context("admin"))
    return _respond(start_response, html_response(body))


def handle_admin_login_post(environ, start_response):
    data = parse_form(environ)
    password = data.get("password", "")
    if auth.check_password(password):
        cookie = auth.session_cookie_header()
        start_response("302 Found", [("Location", "/admin"), cookie])
        return [b""]
    body = render_template("admin_login.html", error="Неверный пароль", **_nav_context("admin"))
    return _respond(start_response, html_response(body, "401 Unauthorized"))


def handle_admin_logout(environ, start_response):
    cookie = auth.logout_cookie_header()
    start_response("302 Found", [("Location", "/admin/login"), cookie])
    return [b""]


def _build_admin_context(link_id=None) -> dict:
    ctx = _nav_context("admin")
    all_links = links.list_all_links()
    ctx["links_rows"] = _render_links_table(all_links)
    ctx["total_links"] = str(len(all_links))
    ctx["clicks_today"] = str(stats.clicks_total_today())
    ctx["stats_section"] = ""
    ctx["link_id"] = ""
    if link_id:
        ctx.update(_build_stats_section(link_id))
    return ctx


def _render_links_table(all_links) -> str:
    if not all_links:
        return '<tr><td colspan="5" class="empty">Пока нет ссылок</td></tr>'
    rows = []
    for l in all_links:
        exp = l.get("expires_at") or "—"
        url = l["original_url"]
        url_show = (url[:60] + "…") if len(url) > 60 else url
        rows.append(
            f'<tr>'
            f'<td><code>{l["slug"]}</code></td>'
            f'<td class="url-cell" title="{html.escape(url, quote=True)}">{html.escape(url_show)}</td>'
            f'<td>{l["click_count"]}</td>'
            f'<td>{exp[:10] if exp != "—" else exp}</td>'
            f'<td><a class="btn-ghost btn-sm" href="/admin/links?id={l["id"]}">Статистика</a></td>'
            f'</tr>'
        )
    return "\n".join(rows)


def _build_stats_section(link_id: int) -> dict:
    link = links.get_link_by_id(link_id)
    if not link:
        return {"stats_section": "", "link_id": ""}
    daily = stats.stats_by_day(link_id, 30)
    referers = stats.top_referers(link_id)
    ref_rows = ""
    for r in referers:
        ref_rows += f'<tr><td>{r["referer"]}</td><td>{r["count"]}</td></tr>'
    if not ref_rows:
        ref_rows = '<tr><td colspan="2" class="empty">Нет данных</td></tr>'

    chart_data = html.escape(json.dumps(daily, ensure_ascii=False), quote=True)
    return {
        "link_id": str(link_id),
        "stats_section": render_template(
            "partials/stats_section.html",
            slug=link["slug"],
            short_url=f"{config.BASE_URL}/{link['slug']}",
            original_url=link["original_url"],
            chart_data=chart_data,
            referer_rows=ref_rows,
            link_id=str(link_id),
        ),
    }


def handle_admin_dashboard(environ, start_response):
    denied = _require_admin(environ, start_response)
    if denied:
        return _respond(start_response, denied)
    body = render_template("admin.html", **_build_admin_context())
    return _respond(start_response, html_response(body))


def handle_admin_link_stats(environ, start_response):
    denied = _require_admin(environ, start_response)
    if denied:
        return _respond(start_response, denied)
    q = parse_query(environ)
    link_id = int(q.get("id", "0") or "0")
    body = render_template("admin.html", **_build_admin_context(link_id=link_id))
    return _respond(start_response, html_response(body))


def handle_api_link_stats(environ, start_response):
    denied = _require_admin(environ, start_response)
    if denied:
        return _respond(start_response, json_response({"error": "Unauthorized"}, "401 Unauthorized"))
    q = parse_query(environ)
    link_id = int(q.get("id", "0"))
    days = int(q.get("days", "30"))
    return _respond(start_response, json_response({
        "data": stats.stats_by_day(link_id, days),
    }))


def handle_api_clicks_csv(environ, start_response):
    denied = _require_admin(environ, start_response)
    if denied:
        return _respond(start_response, csv_response("", "error.csv"))
    q = parse_query(environ)
    link_id = int(q.get("id", "0"))
    content = stats.clicks_for_link_csv(link_id)
    return _respond(start_response, csv_response(content, f"clicks_{link_id}.csv"))


def handle_export_all_csv(environ, start_response):
    denied = _require_admin(environ, start_response)
    if denied:
        return _respond(start_response, csv_response("", "error.csv"))
    content = stats.export_all_csv()
    return _respond(start_response, csv_response(content, "superlinker_all_stats.csv"))


def handle_generate_test_data(environ, start_response):
    denied = _require_admin(environ, start_response)
    if denied:
        return _respond(start_response, json_response({"error": "Unauthorized"}, "401 Unauthorized"))
    result = test_data.generate_test_data(30)
    return _respond(start_response, json_response(result))


def handle_clear_test_data(environ, start_response):
    denied = _require_admin(environ, start_response)
    if denied:
        return _respond(start_response, json_response({"error": "Unauthorized"}, "401 Unauthorized"))
    result = test_data.clear_test_data()
    return _respond(start_response, json_response(result))
