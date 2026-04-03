"""Tests for ai_slopcheck/engine/api_routes.py."""
from __future__ import annotations

from pathlib import Path

from ai_slopcheck.engine.api_routes import (
    extract_all_routes,
    extract_routes_from_file,
)

# ---------------------------------------------------------------------------
# FastAPI
# ---------------------------------------------------------------------------


def test_fastapi_get_route() -> None:
    content = '@app.get("/users")\ndef list_users():\n    pass\n'
    routes = extract_routes_from_file("src/main.py", content)
    assert len(routes) == 1
    r = routes[0]
    assert r.method == "GET"
    assert r.path == "/users"
    assert r.file == "src/main.py"
    assert r.line == 1
    assert r.handler == "list_users"


def test_fastapi_post_route_with_router() -> None:
    content = '@router.post("/items/{item_id}")\ndef create_item(item_id: int):\n    pass\n'
    routes = extract_routes_from_file("api/items.py", content)
    assert len(routes) == 1
    r = routes[0]
    assert r.method == "POST"
    assert r.path == "/items/{item_id}"


def test_fastapi_multiple_routes() -> None:
    content = (
        '@app.get("/a")\ndef get_a(): pass\n'
        '@app.delete("/b")\ndef del_b(): pass\n'
    )
    routes = extract_routes_from_file("src/api.py", content)
    methods = {r.method for r in routes}
    assert "GET" in methods
    assert "DELETE" in methods
    assert len(routes) == 2


def test_fastapi_put_and_patch() -> None:
    content = '@app.put("/x")\n@app.patch("/y")\n'
    routes = extract_routes_from_file("app.py", content)
    assert len(routes) == 2
    assert {r.method for r in routes} == {"PUT", "PATCH"}


# ---------------------------------------------------------------------------
# Flask
# ---------------------------------------------------------------------------


def test_flask_get_route_default_method() -> None:
    content = '@app.route("/home")\ndef home():\n    return "ok"\n'
    routes = extract_routes_from_file("views.py", content)
    assert len(routes) == 1
    assert routes[0].method == "GET"
    assert routes[0].path == "/home"


def test_flask_post_explicit_method() -> None:
    content = '@app.route("/login", methods=["POST"])\ndef login():\n    pass\n'
    routes = extract_routes_from_file("views.py", content)
    assert len(routes) == 1
    assert routes[0].method == "POST"


def test_flask_blueprint_route() -> None:
    content = '@bp.route("/dashboard")\ndef dashboard():\n    pass\n'
    routes = extract_routes_from_file("views.py", content)
    assert len(routes) == 1
    assert routes[0].path == "/dashboard"


# ---------------------------------------------------------------------------
# Express / Hono
# ---------------------------------------------------------------------------


def test_express_get_route() -> None:
    content = 'app.get("/users", (req, res) => res.json([]));\n'
    routes = extract_routes_from_file("server.js", content)
    assert len(routes) == 1
    assert routes[0].method == "GET"
    assert routes[0].path == "/users"


def test_express_post_route() -> None:
    content = 'router.post("/items", createItem);\n'
    routes = extract_routes_from_file("routes/items.js", content)
    assert len(routes) == 1
    assert routes[0].method == "POST"
    assert routes[0].path == "/items"


def test_express_typescript_backtick() -> None:
    content = "app.get(`/api/v1/ping`, handler);\n"
    routes = extract_routes_from_file("app.ts", content)
    assert len(routes) == 1
    assert routes[0].method == "GET"
    assert routes[0].path == "/api/v1/ping"


def test_express_multiple_methods() -> None:
    content = (
        'app.get("/a", h1);\n'
        'app.put("/b", h2);\n'
        'app.delete("/c", h3);\n'
    )
    routes = extract_routes_from_file("app.js", content)
    assert len(routes) == 3
    assert {r.method for r in routes} == {"GET", "PUT", "DELETE"}


# ---------------------------------------------------------------------------
# Next.js App Router
# ---------------------------------------------------------------------------


def test_nextjs_export_get() -> None:
    content = "export async function GET(request: Request) {\n  return Response.json({});\n}\n"
    routes = extract_routes_from_file("app/api/users/route.ts", content)
    assert len(routes) == 1
    r = routes[0]
    assert r.method == "GET"
    assert r.path == "/api/users"
    assert r.handler == "GET"


def test_nextjs_export_post() -> None:
    content = "export function POST(req: Request) {\n  return new Response('ok');\n}\n"
    routes = extract_routes_from_file("app/api/items/[id]/route.ts", content)
    assert len(routes) == 1
    r = routes[0]
    assert r.method == "POST"
    assert r.path == "/api/items/{id}"


def test_nextjs_multiple_methods() -> None:
    content = (
        "export async function GET(req: Request) {}\n"
        "export async function POST(req: Request) {}\n"
    )
    routes = extract_routes_from_file("app/api/orders/route.ts", content)
    assert len(routes) == 2
    assert {r.method for r in routes} == {"GET", "POST"}


def test_nextjs_non_route_file_uses_express_extractor() -> None:
    """A .ts file that is not named route.ts should use Express extractor."""
    content = 'app.get("/ping", handler);\n'
    routes = extract_routes_from_file("src/app.ts", content)
    assert len(routes) == 1
    assert routes[0].method == "GET"


# ---------------------------------------------------------------------------
# Go net/http
# ---------------------------------------------------------------------------


def test_go_handlefunc() -> None:
    content = 'mux.HandleFunc("/api/health", healthHandler)\n'
    routes = extract_routes_from_file("main.go", content)
    assert len(routes) == 1
    assert routes[0].path == "/api/health"
    assert routes[0].method == "ANY"


def test_go_handle() -> None:
    content = 'mux.Handle("/static/", http.StripPrefix("/static/", fs))\n'
    routes = extract_routes_from_file("server.go", content)
    assert len(routes) == 1
    assert routes[0].path == "/static/"


def test_go_multiple_routes() -> None:
    content = (
        'mux.HandleFunc("/users", usersHandler)\n'
        'mux.HandleFunc("/users/{id}", userHandler)\n'
    )
    routes = extract_routes_from_file("handlers.go", content)
    assert len(routes) == 2
    paths = {r.path for r in routes}
    assert "/users" in paths
    assert "/users/{id}" in paths


# ---------------------------------------------------------------------------
# extract_all_routes (integration)
# ---------------------------------------------------------------------------


def test_extract_all_routes_from_tmp_files(tmp_path: Path) -> None:
    py_file = tmp_path / "api.py"
    py_file.write_text('@app.get("/ping")\ndef ping(): pass\n', encoding="utf-8")

    js_file = tmp_path / "server.js"
    js_file.write_text('app.post("/items", create);\n', encoding="utf-8")

    routes = extract_all_routes(tmp_path, [py_file, js_file])
    assert len(routes) == 2
    methods = {r.method for r in routes}
    assert "GET" in methods
    assert "POST" in methods


def test_extract_all_routes_skips_unreadable(tmp_path: Path) -> None:
    missing = tmp_path / "ghost.py"
    # File does not exist — should be silently skipped
    routes = extract_all_routes(tmp_path, [missing])
    assert routes == []


# ---------------------------------------------------------------------------
# Unknown/unsupported extension
# ---------------------------------------------------------------------------


def test_unsupported_extension_returns_empty() -> None:
    content = '@app.get("/x")\n'
    routes = extract_routes_from_file("data.csv", content)
    assert routes == []
