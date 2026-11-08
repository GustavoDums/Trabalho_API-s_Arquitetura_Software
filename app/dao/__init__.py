"""Objetos de acesso a dados (DAO): único ponto de acesso ao SQLite."""

from .cliente_dao import ClienteDAO
from .pedido_dao import PedidoDAO
from .produto_dao import ProdutoDAO

__all__ = ["ClienteDAO", "ProdutoDAO", "PedidoDAO"]

