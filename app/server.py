import json
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from app.dao import ClienteDAO, PedidoDAO, ProdutoDAO
from app.database import connection
from app.models import Cliente, Pedido, Produto
from app.models.validation import ValidationError


RESOURCES = {
    "clientes": (Cliente, ClienteDAO),
    "produtos": (Produto, ProdutoDAO),
    "pedidos": (Pedido, PedidoDAO),
}
MAX_BODY_BYTES = 1_048_576


def make_handler(database_path: str | Path, resource_name: str):
    class APIHandler(BaseHTTPRequestHandler):
        def _json(self, status: int, data: object, location: str | None = None):
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            if location:
                self.send_header("Location", location)
            self.end_headers()
            self.wfile.write(body)

        def _error(self, status: int, message: str):
            self._json(status, {"erro": message})

        def _route(self):
            path = urlsplit(self.path).path.rstrip("/")
            parts = path.split("/")
            if len(parts) not in (2, 3) or parts[0] != "":
                return None
            resource = RESOURCES.get(parts[1]) if parts[1] == resource_name else None
            if resource is None:
                return None
            if len(parts) == 2:
                return parts[1], resource, None
            if not parts[2].isdecimal() or int(parts[2]) <= 0:
                return None
            return parts[1], resource, int(parts[2])

        def _payload(self):
            if self.headers.get_content_type() != "application/json":
                raise ValidationError("Use Content-Type: application/json.")
            raw_length = self.headers.get("Content-Length")
            try:
                length = int(raw_length)
            except (TypeError, ValueError) as exc:
                raise ValidationError("Content-Length inválido.") from exc
            if length <= 0 or length > MAX_BODY_BYTES:
                raise ValidationError("O corpo deve ter entre 1 byte e 1 MiB.")
            try:
                return json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValidationError("Corpo JSON inválido.") from exc

        def _handle(self, method: str):
            route = self._route()
            if route is None:
                self._error(404, "Rota não encontrada.")
                return
            name, (model, dao_type), item_id = route
            allowed = ("GET", "POST") if item_id is None else ("GET", "PUT", "DELETE")
            if method not in allowed:
                self.send_response(405)
                self.send_header("Allow", ", ".join(allowed))
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            try:
                item = model.from_payload(self._payload()) if method in ("POST", "PUT") else None
                with connection(database_path) as db:
                    dao = dao_type(db)
                    if method == "GET" and item_id is None:
                        self._json(200, [row.to_dict() for row in dao.list_all()])
                    elif method == "GET":
                        found = dao.get(item_id)
                        if found is None:
                            self._error(404, "Registro não encontrado.")
                        else:
                            self._json(200, found.to_dict())
                    elif method == "POST":
                        created = dao.create(item)
                        self._json(201, created.to_dict(), f"/{name}/{created.id}")
                    elif method == "PUT":
                        updated = dao.update(item_id, item)
                        if updated is None:
                            self._error(404, "Registro não encontrado.")
                        else:
                            self._json(200, updated.to_dict())
                    else:
                        if dao.delete(item_id):
                            self.send_response(204)
                            self.send_header("Content-Length", "0")
                            self.end_headers()
                        else:
                            self._error(404, "Registro não encontrado.")
            except ValidationError as exc:
                self._error(400, str(exc))
            except sqlite3.IntegrityError as exc:
                if "UNIQUE constraint failed: clientes.email" in str(exc):
                    self._error(409, "Já existe um cliente com este email.")
                elif "FOREIGN KEY constraint failed" in str(exc):
                    self._error(409, "Registro usado por um pedido; exclua o pedido antes.")
                else:
                    self._error(409, "Conflito de integridade dos dados.")

        def do_GET(self):
            self._handle("GET")

        def do_POST(self):
            self._handle("POST")

        def do_PUT(self):
            self._handle("PUT")

        def do_DELETE(self):
            self._handle("DELETE")

    return APIHandler


def create_server(
    host: str, port: int, database_path: str | Path, resource_name: str
) -> ThreadingHTTPServer:
    if resource_name not in RESOURCES:
        raise ValueError(f"API desconhecida: {resource_name}")
    return ThreadingHTTPServer((host, port), make_handler(database_path, resource_name))

