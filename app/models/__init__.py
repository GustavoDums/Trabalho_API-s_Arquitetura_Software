"""Modelos e validação dos recursos da API."""

from .cliente import Cliente
from .pedido import Pedido
from .produto import Produto

__all__ = ["Cliente", "Produto", "Pedido"]

