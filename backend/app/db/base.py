from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe declarativa base de onde todos os modelos ORM herdam.

    Mantida em um módulo próprio (sem importar `app.models`) para evitar import
    circular: os modelos importam `Base` daqui, e o `Base.metadata` só enxerga
    todas as tabelas depois que `app.models` for importado ao menos uma vez
    (ver `app/models/__init__.py`).
    """
