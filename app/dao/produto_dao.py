from app.models import Produto

from .base import BaseDAO


class ProdutoDAO(BaseDAO):
    table = "produtos"
    columns = ("nome", "preco_centavos")
    model = Produto

