from dataclasses import asdict, dataclass
from typing import Any

from .validation import fields, positive_int, text


@dataclass(frozen=True)
class Produto:
    id: int | None
    nome: str
    preco_centavos: int

    @classmethod
    def from_payload(cls, data: Any) -> "Produto":
        fields(data, {"nome", "preco_centavos"})
        return cls(
            None,
            text(data["nome"], "nome", 120),
            positive_int(data["preco_centavos"], "preco_centavos"),
        )

    def to_dict(self) -> dict:
        return asdict(self)

