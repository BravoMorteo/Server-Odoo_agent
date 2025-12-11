# server.py
import os
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Cargar variables de entorno del archivo .env
load_dotenv()

from odoo_client import OdooClient
from tools import load_all

# -----------------------------
# Helpers de inicialización
# -----------------------------
mcp = FastMCP("OdooMCP")  # transporte streamable-http en la app ASGI abajo
deps: Dict[str, Any] = {}
_tools_loaded = False


def init_tools_once() -> None:
    """Carga cliente Odoo y registra tools modulares una sola vez (idempotente)."""
    global _tools_loaded
    if _tools_loaded:
        return
    required = ["ODOO_URL", "ODOO_DB", "ODOO_LOGIN", "ODOO_API_KEY"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        # No abortamos el arranque para que /health funcione; pero logueamos.
        print(f"[WARN] missing envs: {missing}")
    deps["odoo"] = OdooClient()
    load_all(mcp, deps)
    _tools_loaded = True
    print("[INFO] MCP tools registered.")


def _odoo():
    init_tools_once()
    return deps["odoo"]


def _odoo_form_url(model: str, rec_id: int) -> str:
    base = os.environ.get("ODOO_URL", "").rstrip("/")
    if not base:
        return f"odoo://{model}/{rec_id}"
    return f"{base}/web#id={rec_id}&model={model}&view_type=form"


def _encode_content(obj: Any) -> Dict[str, Any]:
    """Envuelve en content array (1 item, type=text, JSON-encoded string)."""
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(obj, ensure_ascii=False),
            }
        ]
    }


def _wants_projects(q: str) -> bool:
    ql = q.lower()
    return any(t in ql for t in ("proyecto", "proyectos", "project", "projects"))


def _wants_tasks(q: str) -> bool:
    ql = q.lower()
    return any(t in ql for t in ("tarea", "tareas", "task", "tasks"))


# -----------------------------
# Tools existentes (autoload)
# -----------------------------
# Nota: el autoload de tools (projects.py / tasks.py) ocurre en init_tools_once()

# -----------------------------
# NUEVOS TOOLS: search y fetch
# -----------------------------


@mcp.tool(
    name="search",
    description="Busca en Odoo proyectos y/o tareas según el query. Devuelve results[] con id/title/url.",
)
def mcp_search(query: str, limit: int = 10) -> Dict[str, Any]:
    """
    Args:
        query: cadena de búsqueda (ilike)
        limit: máximo de resultados total

    Returns (content array, type=text, JSON string):
      {"results":[{"id":"project:1","title":"Project · X","url":"..."},
                  {"id":"task:2","title":"Task · Y","url":"..."}]}
    """
    odoo = _odoo()
    want_p = _wants_projects(query)
    want_t = _wants_tasks(query)
    if not (want_p or want_t):
        # Si no detecta, buscamos en ambos
        want_p = want_t = True

    # Dividimos el límite (p. ej. mitad y mitad) si se buscan ambos
    lim_p = limit if want_p and not want_t else max(1, limit // 2) if want_p else 0
    lim_t = limit if want_t and not want_p else max(1, limit // 2) if want_t else 0

    results: List[Dict[str, Any]] = []

    if want_p and lim_p:
        domain = [["name", "ilike", query]] if query else []
        rows = odoo.search_read(
            "project.project", domain, ["id", "name", "active"], lim_p
        )
        for r in rows:
            pid = int(r["id"])
            results.append(
                {
                    "id": f"project:{pid}",
                    "title": f"Project · {r.get('name','(sin nombre)')}",
                    "url": _odoo_form_url("project.project", pid),
                }
            )

    if want_t and lim_t:
        domain = [["name", "ilike", query]] if query else []
        rows = odoo.search_read(
            "project.task",
            domain,
            ["id", "name", "project_id", "user_id", "stage_id", "date_deadline"],
            lim_t,
        )
        for r in rows:
            tid = int(r["id"])
            results.append(
                {
                    "id": f"task:{tid}",
                    "title": f"Task · {r.get('name','(sin nombre)')}",
                    "url": _odoo_form_url("project.task", tid),
                }
            )

    return _encode_content({"results": results})


@mcp.tool(
    name="fetch",
    description="Recupera el documento completo por id (project:<id> o task:<id>) con texto y metadatos.",
)
def mcp_fetch(doc_id: str) -> Dict[str, Any]:
    """
    Args:
        doc_id: "project:<id>" o "task:<id>"

    Returns (content array, type=text, JSON string):
      {"id":"task:123","title":"...","text":"...","url":"...","metadata":{...}}
    """
    odoo = _odoo()
    if ":" not in doc_id:
        return _encode_content(
            {"error": "Invalid id format. Use 'project:<id>' or 'task:<id>'."}
        )

    kind, raw_id = doc_id.split(":", 1)
    try:
        rid = int(raw_id)
    except ValueError:
        return _encode_content({"error": "Invalid numeric id."})

    if kind == "project":
        rows = odoo.search_read(
            "project.project", [["id", "=", rid]], ["id", "name", "active"], 1
        )
        if not rows:
            return _encode_content({"error": f"Project {rid} not found"})
        r = rows[0]
        title = f"Project · {r.get('name','(sin nombre)')}"
        text = r.get("name", "")
        url = _odoo_form_url("project.project", rid)
        doc = {
            "id": f"project:{rid}",
            "title": title,
            "text": text,
            "url": url,
            "metadata": {"model": "project.project", "active": r.get("active", True)},
        }
        return _encode_content(doc)

    if kind == "task":
        rows = odoo.search_read(
            "project.task",
            [["id", "=", rid]],
            [
                "id",
                "name",
                "project_id",
                "user_id",
                "stage_id",
                "date_deadline",
                "description",
            ],
            1,
        )
        if not rows:
            return _encode_content({"error": f"Task {rid} not found"})
        r = rows[0]
        title = f"Task · {r.get('name','(sin nombre)')}"
        text = (r.get("description") or r.get("name") or "").strip()
        url = _odoo_form_url("project.task", rid)
        # project_id/user_id/stage_id suelen venir como [id, "Nombre"]
        meta: Dict[str, Any] = {"model": "project.task"}
        for key in ("project_id", "user_id", "stage_id"):
            val = r.get(key)
            if isinstance(val, list) and len(val) >= 1:
                meta[key] = {"id": val[0], "name": val[1] if len(val) > 1 else None}
            else:
                meta[key] = val
        meta["date_deadline"] = r.get("date_deadline")
        doc = {
            "id": f"task:{rid}",
            "title": title,
            "text": text,
            "url": url,
            "metadata": meta,
        }
        return _encode_content(doc)

    return _encode_content(
        {"error": f"Unknown kind '{kind}'. Use 'project' or 'task'."}
    )


# -----------------------------
# ASGI: Composite (health + MCP)
# -----------------------------
mcp_app = mcp.streamable_http_app()  # app ASGI del MCP (SSE)


async def app(scope, receive, send):
    # Health para App Runner
    if scope["type"] == "http" and scope.get("path") == "/health":
        body = b'{"ok": true}'
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"application/json")],
            }
        )
        await send({"type": "http.response.body", "body": body})
        return

    # Primer request real: registra tools modulares
    if not _tools_loaded:
        try:
            init_tools_once()
        except Exception as e:
            if scope["type"] == "http":
                msg = json.dumps(
                    {"error": f"init_tools_once failed: {repr(e)}"}
                ).encode("utf-8")
                await send(
                    {
                        "type": "http.response.start",
                        "status": 500,
                        "headers": [(b"content-type", b"application/json")],
                    }
                )
                await send({"type": "http.response.body", "body": msg})
                return
            raise

    # Todo lo demás lo maneja el servidor MCP (Streamable HTTP)
    await mcp_app(scope, receive, send)


# Local run
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
