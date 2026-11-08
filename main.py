import argparse
from pathlib import Path

from app.database import initialize
from app.server import create_server


DEFAULT_PORTS = {"clientes": 8001, "produtos": 8002, "pedidos": 8003}


def run(resource_name: str, argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description=f"API de {resource_name}")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORTS[resource_name])
    parser.add_argument("--database", type=Path, default=Path("data/api.sqlite3"))
    args = parser.parse_args(argv)

    initialize(args.database)
    server = create_server(args.host, args.port, args.database, resource_name)
    print(f"API de {resource_name}: http://{args.host}:{server.server_port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Iniciar uma das três APIs")
    parser.add_argument("api", choices=DEFAULT_PORTS)
    args, remaining = parser.parse_known_args()
    run(args.api, remaining)
