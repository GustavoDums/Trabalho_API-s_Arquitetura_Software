import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

from app.database import initialize
from app.server import create_server


class APITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        database = Path(cls.tmp.name) / "test.sqlite3"
        initialize(database)
        cls.servers = {}
        cls.threads = []
        for resource in ("clientes", "produtos", "pedidos"):
            server = create_server("127.0.0.1", 0, database, resource)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            cls.servers[resource] = server
            cls.threads.append(thread)

    @classmethod
    def tearDownClass(cls):
        for server in cls.servers.values():
            server.shutdown()
            server.server_close()
        for thread in cls.threads:
            thread.join()
        cls.tmp.cleanup()

    def request(self, method, path, payload=None, raw=None, content_type="application/json", api=None):
        resource = api or path.split("/")[1]
        server = self.servers.get(resource, self.servers["clientes"])
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        body = raw if raw is not None else json.dumps(payload).encode() if payload is not None else None
        headers = {"Content-Type": content_type} if body is not None else {}
        try:
            conn.request(method, path, body=body, headers=headers)
            response = conn.getresponse()
            data = response.read()
            return response.status, dict(response.getheaders()), json.loads(data) if data else None
        finally:
            conn.close()

    def test_crud_and_relations(self):
        status, headers, cliente = self.request(
            "POST", "/clientes", {"nome": "Ana", "email": "ana@example.com"}
        )
        self.assertEqual(status, 201)
        self.assertEqual(headers["Location"], f"/clientes/{cliente['id']}")
        status, _, produto = self.request(
            "POST", "/produtos", {"nome": "Caderno", "preco_centavos": 2590}
        )
        self.assertEqual(status, 201)
        status, _, pedido = self.request(
            "POST", "/pedidos", {"cliente_id": cliente["id"], "produto_id": produto["id"], "quantidade": 2}
        )
        self.assertEqual(status, 201)
        self.assertEqual(pedido["total_centavos"], 5180)

        for resource, item in (("clientes", cliente), ("produtos", produto), ("pedidos", pedido)):
            with self.subTest(resource=resource):
                self.assertEqual(self.request("GET", f"/{resource}/{item['id']}")[2], item)
                self.assertIn(item, self.request("GET", f"/{resource}")[2])

        status, _, _ = self.request("DELETE", f"/clientes/{cliente['id']}")
        self.assertEqual(status, 409)
        status, _, _ = self.request("DELETE", f"/produtos/{produto['id']}")
        self.assertEqual(status, 409)

        status, _, updated = self.request(
            "PUT", f"/clientes/{cliente['id']}", {"nome": "Ana Souza", "email": "ana@example.com"}
        )
        self.assertEqual((status, updated["nome"]), (200, "Ana Souza"))
        status, _, updated = self.request(
            "PUT", f"/produtos/{produto['id']}", {"nome": "Caderno", "preco_centavos": 3000}
        )
        self.assertEqual((status, updated["preco_centavos"]), (200, 3000))
        self.assertEqual(self.request("GET", f"/pedidos/{pedido['id']}")[2]["total_centavos"], 5180)
        status, _, updated = self.request(
            "PUT", f"/pedidos/{pedido['id']}", {"cliente_id": cliente["id"], "produto_id": produto["id"], "quantidade": 3}
        )
        self.assertEqual((status, updated["total_centavos"]), (200, 9000))

        for resource, item in (("pedidos", pedido), ("produtos", produto), ("clientes", cliente)):
            with self.subTest(deleting=resource):
                status, _, body = self.request("DELETE", f"/{resource}/{item['id']}")
                self.assertEqual((status, body), (204, None))
                self.assertEqual(self.request("GET", f"/{resource}/{item['id']}")[0], 404)

    def test_invalid_requests_and_conflict(self):
        self.assertEqual(self.request("POST", "/clientes", {"nome": "Sem email"})[0], 400)
        self.assertEqual(self.request("POST", "/produtos", {"nome": "X", "preco_centavos": True})[0], 400)
        self.assertEqual(self.request("POST", "/clientes", raw=b"{")[0], 400)
        self.assertEqual(self.request("POST", "/clientes", {"nome": "A", "email": "a@b"}, content_type="text/plain")[0], 400)
        self.assertEqual(self.request("POST", "/pedidos", {"cliente_id": 999, "produto_id": 999, "quantidade": 1})[0], 400)
        self.assertEqual(self.request("PUT", "/produtos/999", {"nome": "X", "preco_centavos": 100})[0], 404)
        self.assertEqual(self.request("DELETE", "/pedidos/999")[0], 404)
        self.assertEqual(self.request("POST", "/clientes/1", {"nome": "X", "email": "x@y"})[0], 405)
        self.assertEqual(self.request("GET", "/desconhecido")[0], 404)
        self.assertEqual(self.request("GET", "/produtos", api="clientes")[0], 404)

        data = {"nome": "Cliente", "email": "duplicado@example.com"}
        self.assertEqual(self.request("POST", "/clientes", data)[0], 201)
        self.assertEqual(self.request("POST", "/clientes", data)[0], 409)


if __name__ == "__main__":
    unittest.main()
