from dataclasses import asdict, dataclass
import re
from typing import Any

from .validation import ValidationError, fields, text


@dataclass(frozen=True)
class Cliente:
    id: int | None
    nome: str
    email: str

    @classmethod
    def from_payload(cls, data: Any) -> "Cliente":
        fields(data, {"nome", "email"})
        nome = text(data["nome"], "nome", 120)
        email = text(data["email"], "email", 255).lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s.]+(?:\.[^@\s.]+)+", email):
            raise ValidationError("email deve ser um endereço válido.")
        return cls(None, nome, email)

    def to_dict(self) -> dict:
        return asdict(self)

