from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """Classe declarativa base de onde todos os modelos ORM herdam.

    Mantida em um módulo próprio (sem importar `app.models`) para evitar import
    circular: os modelos importam `Base` daqui, e o `Base.metadata` só enxerga
    todas as tabelas depois que `app.models` for importado ao menos uma vez
    (ver `app/models/__init__.py`).

    `AsyncAttrs` (issue #8) dá a todo modelo um `.awaitable_attrs`, usado em
    `app/repositories/atendimento.py::list_by_paciente` para disparar lazy loading de
    forma explícita com `await` — com `AsyncSession`, acessar um atributo lazy
    (`obj.relacionamento`) fora de uma corrotina quebra com `MissingGreenlet`; o
    `awaitable_attrs` é a forma suportada de fazer lazy load "de propósito" em código
    assíncrono.
    """
