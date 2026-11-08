from app.models import Cliente

from .base import BaseDAO


class ClienteDAO(BaseDAO):
    table = "clientes"
    columns = ("nome", "email")
    model = Cliente

