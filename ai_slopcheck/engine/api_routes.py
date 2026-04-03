"""Extract API route definitions from source files."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RouteDefinition:
    method: str   # GET, POST, PUT, DELETE, PATCH
    path: str     # /api/users/{id}
    file: str     # relative path
    line: int     # 1-indexed
    handler: str  # function name (if detectable)


# FastAPI: @app.get("/path") or @router.post("/path")
_FASTAPI_RE = re.compile(
    r"@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)

# Flask: @app.route("/path", methods=["GET"]) or @bp.route(...)
_FLASK_RE = re.compile(
    r"@(?:app|blueprint|bp)\.route\s*\(\s*['\"]([^'\"]+)['\"]"
    r"(?:[^)]*methods\s*=\s*\[\s*['\"]([A-Z]+)['\"])?",
    re.IGNORECASE,
)

# Express/Hono: app.get("/path", ...) or router.post("/path", ...)
_EXPRESS_RE = re.compile(
    r"(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['\"`]([^'\"` \n]+)['\"`]",
    re.IGNORECASE,
)

# Next.js App Router: export async function GET(...) or export function POST(...)
_NEXTJS_EXPORT_RE = re.compile(
    r"export\s+(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH)\b",
)

# Go net/http: mux.HandleFunc("/path", handler) or mux.Handle("/path", ...)
_GO_HANDLEFUNC_RE = re.compile(
    r"\.HandleFunc\s*\(\s*\"([^\"]+)\"",
)
_GO_HANDLE_RE = re.compile(
    r"\.Handle\s*\(\s*\"([^\"]+)\"",
)

# Python def line after a route decorator
_PY_DEF_RE = re.compile(r"^[ \t]*def\s+(\w+)\s*\(")

# JS/TS function/arrow after a route call
_JS_HANDLER_RE = re.compile(r"(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=)")


def _nextjs_path_from_file(relative_path: str) -> str:
    """Derive the route path from a Next.js App Router file path.

    e.g. app/api/users/[id]/route.ts  ->  /api/users/[id]
    """
    p = Path(relative_path)
    parts = list(p.parts)

    # Drop the filename (route.ts / route.js)
    parts = parts[:-1]

    # Find the "app" segment and drop everything before it
    try:
        app_idx = parts.index("app")
        parts = parts[app_idx + 1:]
    except ValueError:
        pass  # No "app" prefix found – use as-is

    # Convert [param] to {param} for consistency
    normalised = []
    for part in parts:
        if part.startswith("[") and part.endswith("]"):
            normalised.append("{" + part[1:-1] + "}")
        else:
            normalised.append(part)

    return "/" + "/".join(normalised) if normalised else "/"


def _is_nextjs_route_file(relative_path: str) -> bool:
    p = Path(relative_path)
    return p.name in {"route.ts", "route.js", "route.tsx", "route.jsx"}


def _extract_fastapi(relative_path: str, lines: list[str]) -> list[RouteDefinition]:
    results: list[RouteDefinition] = []
    for i, line in enumerate(lines, start=1):
        m = _FASTAPI_RE.search(line)
        if m:
            method = m.group(1).upper()
            path = m.group(2)
            # Look for the def on the next non-blank line
            handler = ""
            for j in range(i, min(i + 3, len(lines))):
                dm = _PY_DEF_RE.match(lines[j])
                if dm:
                    handler = dm.group(1)
                    break
            results.append(RouteDefinition(
                method=method, path=path, file=relative_path, line=i, handler=handler,
            ))
    return results


def _extract_flask(relative_path: str, lines: list[str]) -> list[RouteDefinition]:
    results: list[RouteDefinition] = []
    for i, line in enumerate(lines, start=1):
        m = _FLASK_RE.search(line)
        if m:
            path = m.group(1)
            method = (m.group(2) or "GET").upper()
            handler = ""
            for j in range(i, min(i + 3, len(lines))):
                dm = _PY_DEF_RE.match(lines[j])
                if dm:
                    handler = dm.group(1)
                    break
            results.append(RouteDefinition(
                method=method, path=path, file=relative_path, line=i, handler=handler,
            ))
    return results


def _extract_express(relative_path: str, lines: list[str]) -> list[RouteDefinition]:
    results: list[RouteDefinition] = []
    for i, line in enumerate(lines, start=1):
        m = _EXPRESS_RE.search(line)
        if m:
            method = m.group(1).upper()
            path = m.group(2)
            results.append(RouteDefinition(
                method=method, path=path, file=relative_path, line=i, handler="",
            ))
    return results


def _extract_nextjs(relative_path: str, lines: list[str]) -> list[RouteDefinition]:
    results: list[RouteDefinition] = []
    route_path = _nextjs_path_from_file(relative_path)
    for i, line in enumerate(lines, start=1):
        m = _NEXTJS_EXPORT_RE.search(line)
        if m:
            method = m.group(1).upper()
            results.append(RouteDefinition(
                method=method, path=route_path, file=relative_path, line=i, handler=method,
            ))
    return results


def _extract_go(relative_path: str, lines: list[str]) -> list[RouteDefinition]:
    results: list[RouteDefinition] = []
    for i, line in enumerate(lines, start=1):
        for pattern in (_GO_HANDLEFUNC_RE, _GO_HANDLE_RE):
            m = pattern.search(line)
            if m:
                path = m.group(1)
                results.append(RouteDefinition(
                    method="ANY", path=path, file=relative_path, line=i, handler="",
                ))
                break  # Only one match per line
    return results


def extract_routes_from_file(relative_path: str, content: str) -> list[RouteDefinition]:
    """Extract route definitions from a single file."""
    lines = content.splitlines()
    ext = Path(relative_path).suffix.lower()

    results: list[RouteDefinition] = []

    if ext == ".py":
        results.extend(_extract_fastapi(relative_path, lines))
        results.extend(_extract_flask(relative_path, lines))
    elif ext in {".ts", ".tsx", ".js", ".jsx"}:
        if _is_nextjs_route_file(relative_path):
            results.extend(_extract_nextjs(relative_path, lines))
        else:
            results.extend(_extract_express(relative_path, lines))
    elif ext == ".go":
        results.extend(_extract_go(relative_path, lines))

    # Deduplicate by (method, path, line) to avoid double-hits
    seen: set[tuple[str, str, int]] = set()
    deduped: list[RouteDefinition] = []
    for r in results:
        key = (r.method, r.path, r.line)
        if key not in seen:
            seen.add(key)
            deduped.append(r)

    return deduped


def extract_all_routes(repo_root: Path, files: list[Path]) -> list[RouteDefinition]:
    """Extract routes from all files in the repo."""
    all_routes: list[RouteDefinition] = []
    for file_path in files:
        try:
            relative_path = file_path.relative_to(repo_root).as_posix()
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            all_routes.extend(extract_routes_from_file(relative_path, content))
        except OSError:
            continue
    return all_routes
