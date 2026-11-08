from dataclasses import asdict, dataclass
from typing import Any

from .validation import fields, positive_int


@dataclass(frozen=True)
class Pedido:
    id: int | None
    cliente_id: int
    produto_id: int
    quantidade: int
    total_centavos: int | None = None

    @classmethod
    def from_payload(cls, data: Any) -> "Pedido":
        fields(data, {"cliente_id", "produto_id", "quantidade"})
        return cls(
            None,
            positive_int(data["cliente_id"], "cliente_id"),
            positive_int(data["produto_id"], "produto_id"),
            positive_int(data["quantidade"], "quantidade"),
        )

    def to_dict(self) -> dict:
        return asdict(self)

