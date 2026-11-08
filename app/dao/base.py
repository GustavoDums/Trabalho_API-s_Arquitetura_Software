import sqlite3


class BaseDAO:
    table: str
    columns: tuple[str, ...]
    model: type

    def __init__(self, db: sqlite3.Connection):
        self.db = db

    def list_all(self) -> list:
        rows = self.db.execute(f"SELECT * FROM {self.table} ORDER BY id").fetchall()
        return [self.model(**dict(row)) for row in rows]

    def get(self, item_id: int):
        row = self.db.execute(
            f"SELECT * FROM {self.table} WHERE id = ?", (item_id,)
        ).fetchone()
        return self.model(**dict(row)) if row else None

    def create(self, item):
        names = ", ".join(self.columns)
        placeholders = ", ".join("?" for _ in self.columns)
        values = tuple(getattr(item, name) for name in self.columns)
        cursor = self.db.execute(
            f"INSERT INTO {self.table} ({names}) VALUES ({placeholders})", values
        )
        return self.get(cursor.lastrowid)

    def update(self, item_id: int, item):
        assignments = ", ".join(f"{name} = ?" for name in self.columns)
        values = tuple(getattr(item, name) for name in self.columns)
        cursor = self.db.execute(
            f"UPDATE {self.table} SET {assignments} WHERE id = ?",
            (*values, item_id),
        )
        return self.get(item_id) if cursor.rowcount else None

    def delete(self, item_id: int) -> bool:
        cursor = self.db.execute(
            f"DELETE FROM {self.table} WHERE id = ?", (item_id,)
        )
        return cursor.rowcount > 0

