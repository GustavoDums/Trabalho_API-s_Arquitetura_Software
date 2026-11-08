from typing import Any


class ValidationError(ValueError):
    """Dados enviados pelo cliente não atendem ao contrato da API."""


def fields(data: Any, expected: set[str]) -> None:
    if not isinstance(data, dict):
        raise ValidationError("O corpo deve ser um objeto JSON.")
    missing = expected - data.keys()
    extra = data.keys() - expected
    if missing or extra:
        parts = []
        if missing:
            parts.append("campos obrigatórios: " + ", ".join(sorted(missing)))
        if extra:
            parts.append("campos desconhecidos: " + ", ".join(sorted(extra)))
        raise ValidationError("; ".join(parts) + ".")


def text(value: Any, name: str, limit: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{name} deve ser um texto não vazio.")
    result = value.strip()
    if len(result) > limit:
        raise ValidationError(f"{name} deve ter no máximo {limit} caracteres.")
    return result


def positive_int(value: Any, name: str) -> int:
    if type(value) is not int or value <= 0:
        raise ValidationError(f"{name} deve ser um inteiro positivo.")
    return value

