from dataclasses import replace

from app.models import Pedido
from app.models.validation import ValidationError

from .base import BaseDAO


class PedidoDAO(BaseDAO):
    table = "pedidos"
    columns = ("cliente_id", "produto_id", "quantidade", "total_centavos")
    model = Pedido

    def _with_total(self, pedido: Pedido) -> Pedido:
        cliente = self.db.execute(
            "SELECT 1 FROM clientes WHERE id = ?", (pedido.cliente_id,)
        ).fetchone()
        if cliente is None:
            raise ValidationError("cliente_id não corresponde a um cliente existente.")
        produto = self.db.execute(
            "SELECT preco_centavos FROM produtos WHERE id = ?", (pedido.produto_id,)
        ).fetchone()
        if produto is None:
            raise ValidationError("produto_id não corresponde a um produto existente.")
        return replace(
            pedido, total_centavos=produto["preco_centavos"] * pedido.quantidade
        )

    def create(self, pedido: Pedido) -> Pedido:
        return super().create(self._with_total(pedido))

    def update(self, item_id: int, pedido: Pedido) -> Pedido | None:
        if self.get(item_id) is None:
            return None
        return super().update(item_id, self._with_total(pedido))

