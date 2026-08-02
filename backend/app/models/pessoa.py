"""`Pessoa` — base da hierarquia de herança joined (Requisito 4 da Etapa 2).

## Herança joined sem coluna discriminadora

O schema (`db/01_schema.sql`) não tem uma coluna `pessoa.tipo` (nem
`profissional.tipo`): a única forma de saber se uma `pessoa` é paciente ou
profissional — ou se um `profissional` é preceptor ou residente — é verificar em qual(is)
tabela(s) filha(s) existe uma linha com a mesma PK. Não podemos adicionar essa coluna
porque `db/` é contrato compartilhado com outros agentes trabalhando em paralelo nas
issues #4, #5 e #6.

O SQLAlchemy permite que `polymorphic_on` seja **qualquer expressão SQL**, não apenas uma
coluna física (documentado em "Configuring the Discriminator" na doc oficial de
inheritance mapping). Usamos isso para construir uma única expressão `CASE` com
subconsultas `EXISTS` correlacionadas às quatro tabelas filhas, cobrindo os dois níveis da
hierarquia (`pessoa` → `paciente`/`profissional` → `preceptor`/`residente`) com um único
discriminador:

```sql
CASE
    WHEN EXISTS (SELECT 1 FROM residente    WHERE residente.id_profissional = pessoa.id_pessoa)    THEN 'residente'
    WHEN EXISTS (SELECT 1 FROM preceptor    WHERE preceptor.id_profissional = pessoa.id_pessoa)    THEN 'preceptor'
    WHEN EXISTS (SELECT 1 FROM profissional WHERE profissional.id_pessoa    = pessoa.id_pessoa)    THEN 'profissional'
    WHEN EXISTS (SELECT 1 FROM paciente     WHERE paciente.id_pessoa        = pessoa.id_pessoa)    THEN 'paciente'
    ELSE 'pessoa'
END
```

As tabelas `paciente`/`profissional`/`preceptor`/`residente` são referenciadas aqui via
`sqlalchemy.table()`/`column()` — construções "leves" do Core que descrevem apenas nome de
tabela e coluna, sem depender das classes ORM (que ainda não existem neste módulo: são
definidas em arquivos separados, um por agregado). Isso evita import circular.

Validado empiricamente contra o banco (ver `backend/tests/test_orm_models.py`
`test_heranca_joined_carrega_subtipo_correto`): `select(Pessoa)` retorna instâncias já
resolvidas como `Paciente`, `Profissional`, `Preceptor` ou `Residente`, conforme a linha.

## Limitações desta abordagem

1. **Custo por linha.** Toda consulta a `Pessoa` (ou a qualquer subtipo, já que a
   expressão é herdada) roda até 4 subconsultas `EXISTS` correlacionadas. Aceitável no
   volume de dados da disciplina; não escalaria como está para uma tabela `pessoa` com
   milhões de linhas — uma coluna discriminadora física seria O(1) por linha.
2. **Não enforce a disjunção.** A `CASE` apenas *decide qual identidade usar para
   instanciar o objeto Python*; ela não impede que a mesma `id_pessoa` exista em
   `paciente` **e** `profissional` ao mesmo tempo (o schema já documenta essa lacuna em
   `docs/modelagem.md`, seção 3.3). Se isso acontecer, a ordem dos `WHEN` favorece
   `profissional`/`residente`/`preceptor` sobre `paciente` — é uma decisão arbitrária de
   desempate, não uma regra de negócio validada.
3. **Acoplamento por nome de tabela, não por FK.** As referências via `table()`/`column()`
   são strings literais (`"paciente"`, `"id_pessoa"`, ...). Renomear uma dessas tabelas ou
   colunas no `db/01_schema.sql` quebra o discriminador silenciosamente em tempo de
   execução (sem erro de import), não em tempo de migração.
4. **`with_polymorphic` é necessário para eager loading dos subtipos.** Uma consulta
   simples `select(Pessoa)` traz só as colunas de `pessoa`; os atributos específicos de
   `Paciente`/`Profissional`/`Preceptor`/`Residente` continuam exigindo lazy load (ou
   `with_polymorphic(Pessoa, "*")` para trazer tudo em um único `LEFT OUTER JOIN`).
"""

from datetime import date

from sqlalchemy import CHAR, Boolean, Date, String, case, column, exists, table
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

_paciente_tbl = table("paciente", column("id_pessoa"))
_profissional_tbl = table("profissional", column("id_pessoa"))
_preceptor_tbl = table("preceptor", column("id_profissional"))
_residente_tbl = table("residente", column("id_profissional"))


class Pessoa(Base):
    __tablename__ = "pessoa"

    id_pessoa: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    cpf: Mapped[str] = mapped_column(CHAR(11), nullable=False, unique=True)
    data_nascimento: Mapped[date] = mapped_column(Date, nullable=False)
    is_flamengo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    telefone: Mapped[str] = mapped_column(String(20), nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": "pessoa",
        "polymorphic_on": case(
            (
                exists().where(_residente_tbl.c.id_profissional == id_pessoa),
                "residente",
            ),
            (
                exists().where(_preceptor_tbl.c.id_profissional == id_pessoa),
                "preceptor",
            ),
            (
                exists().where(_profissional_tbl.c.id_pessoa == id_pessoa),
                "profissional",
            ),
            (
                exists().where(_paciente_tbl.c.id_pessoa == id_pessoa),
                "paciente",
            ),
            else_="pessoa",
        ),
    }

    def __repr__(self) -> str:
        return f"<Pessoa id_pessoa={self.id_pessoa} nome={self.nome!r}>"
