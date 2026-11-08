import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


@contextmanager
def connection(path: str | Path) -> Iterator[sqlite3.Connection]:
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    try:
        with db:
            yield db
    finally:
        db.close()


def initialize(path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connection(path) as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                preco_centavos INTEGER NOT NULL CHECK (preco_centavos > 0)
            );
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE RESTRICT,
                produto_id INTEGER NOT NULL REFERENCES produtos(id) ON DELETE RESTRICT,
                quantidade INTEGER NOT NULL CHECK (quantidade > 0),
                total_centavos INTEGER NOT NULL CHECK (total_centavos > 0)
            );
        """)

