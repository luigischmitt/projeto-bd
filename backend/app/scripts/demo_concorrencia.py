"""Demonstração de concorrência na escala (issue #11, Req 6).

Cenário: duas transações abrem sessões async simultâneas tentando escalar o MESMO
residente para o MESMO dia, turno e unidade — a disputa que
`uq_escala_unidade_dia_turno_residente` (db/01_schema.sql) e
`trg_check_sobreposicao_escala` (db/03_triggers.sql) existem para impedir, mas que só
essas redes de segurança tratariam de forma incompleta (ver `TENTAR_AGENDAR_ESCALA` e o
docstring do módulo mais abaixo).

Estratégia: LOCK PESSIMISTA. A leitura de verificação usa `with_for_update()` dentro da
mesma transação que faz o INSERT, então a segunda transação a chegar fica bloqueada no
banco até a primeira commitar, e só então revalida a condição — com a linha já lá,
rejeitando corretamente.

--------------------------------------------------------------------------------------
O problema de travar uma linha que ainda não existe
--------------------------------------------------------------------------------------
`with_for_update()` (SELECT ... FOR UPDATE) só bloqueia linhas que JÁ EXISTEM no banco.
Aqui as duas transações querem *inserir* uma escala nova — não há linha de `escala` para
travar antes do INSERT, e um SELECT FOR UPDATE sobre `escala` filtrado pela tripla
(unidade, dia, turno, residente) simplesmente não encontraria nada em nenhuma das duas
transações, retornando "livre" para as duas e não serializando coisa nenhuma.

A solução adotada é travar um RECURSO-ÂNCORA que já existe e que é comum às duas
transações concorrentes: a própria linha do RESIDENTE (`SELECT ... FROM residente WHERE
id_profissional = :id FOR UPDATE`). Como o residente é sujeito de ambos os predicados em
disputa — a UNIQUE (mesma unidade/dia/turno/residente) e a trigger (mesmo dia/turno,
residente, unidade diferente) — travar a linha do residente serializa qualquer par de
transações que dispute uma escala envolvendo aquele residente, independente da
combinação exata de unidade/dia/turno. É um lock mais amplo do que o estritamente
necessário para este cenário (travaria também duas tentativas de escalar o MESMO
residente em dias diferentes, que não colidiriam de fato), mas é a âncora mais simples e
correta disponível sem introduzir uma tabela ou lock adicional só para isso.

Alternativa descartada: um advisory lock do Postgres
(`pg_advisory_xact_lock(hashtext(...))`) sobre a chave lógica (id_unidade, dia_semana,
turno, id_residente) seria mais preciso (só serializaria disputas pela MESMA tripla), mas
adiciona uma dependência de uma função de baixo nível do Postgres fora do controle do
ORM e sem relação com nenhuma linha real — para o escopo desta issue, o lock pessimista
sobre uma linha existente e semanticamente relacionada (o residente) é mais direto de
explicar e de auditar no log.

--------------------------------------------------------------------------------------
Por que o lock sozinho não bastaria (a ligação com as triggers)
--------------------------------------------------------------------------------------
O lock pessimista só protege a consistência se a VERIFICAÇÃO e a INSERÇÃO acontecerem
dentro da MESMA transação que segura o lock — exatamete o que `tentar_agendar_escala`
faz abaixo, tudo dentro de um único `session.begin()`. Se o SELECT FOR UPDATE fosse feito
numa transação e o INSERT em outra (ex.: verificação numa request, inserção numa
segunda), o lock seria liberado entre as duas operações e a janela de corrida reabriria:
a transação B poderia ler "livre" logo após A liberar o lock de verificação, mas antes do
INSERT de A ser commitado. É exatamente esse cenário — aplicação que separa checagem de
efeito — que a UNIQUE e a trigger `trg_check_sobreposicao_escala` cobrem como rede de
segurança independente da disciplina da aplicação: mesmo que o lock da aplicação falhe
ou seja usado incorretamente, o banco rejeita a inconsistência no INSERT/UPDATE.

Uso:
    DATABASE_URL=postgresql://postgres:postgres@localhost:55454/hospital_yuska \\
        python -m app.scripts.demo_concorrencia
"""

from __future__ import annotations

import argparse
import asyncio
import time

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.session import async_session_factory
from app.models.escala import Escala
from app.models.residente import Residente

_INICIO = time.monotonic()


def log(rotulo: str, mensagem: str) -> None:
    """Log com carimbo de tempo relativo ao início do script (`t=+SSS.mmm`), para deixar
    o intervalo de bloqueio de B visualmente evidente no terminal e no vídeo da entrega.
    """
    decorrido = time.monotonic() - _INICIO
    print(f"[t=+{decorrido:7.3f}s] {rotulo:<12} {mensagem}", flush=True)


class ConflitoDeEscalaError(Exception):
    """Levantada quando a revalidação pós-lock encontra a vaga já ocupada."""


async def tentar_agendar_escala(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    rotulo: str,
    id_unidade: int,
    dia_semana: str,
    turno: str,
    id_residente: int,
    id_preceptor: int,
    atraso_inicial: float = 0.0,
    atraso_com_lock: float = 0.0,
) -> int:
    """Tenta escalar `id_residente` em (id_unidade, dia_semana, turno) com lock
    pessimista. Retorna o `id_escala` criado em caso de sucesso; levanta
    `ConflitoDeEscalaError` se a revalidação pós-lock encontrar a vaga ocupada.

    `atraso_inicial` simula a transação B chegando um instante depois de A (só para
    tornar a demonstração determinística — sem isso, as duas correndo em paralelo
    poderiam pegar o lock em qualquer ordem, o que não muda a corretude, só a
    previsibilidade do log). `atraso_com_lock` simula A retendo o lock por um tempo
    (o "trabalho" da transação) para que o bloqueio de B fique evidente no carimbo de
    tempo.
    """
    if atraso_inicial:
        await asyncio.sleep(atraso_inicial)

    async with session_factory() as session:
        async with session.begin():
            log(rotulo, f"solicitando lock pessimista na linha do residente {id_residente}")
            await session.execute(
                select(Residente.id_profissional)
                .where(Residente.id_profissional == id_residente)
                .with_for_update()
            )
            log(rotulo, "lock adquirido")

            if atraso_com_lock:
                log(rotulo, f"retendo o lock por {atraso_com_lock:.1f}s (simulando trabalho)")
                await asyncio.sleep(atraso_com_lock)

            log(rotulo, "revalidando condição (unidade, dia, turno, residente) com o lock em mãos")
            conflito = await session.execute(
                select(Escala.id_escala).where(
                    Escala.id_unidade == id_unidade,
                    Escala.dia_semana == dia_semana,
                    Escala.turno == turno,
                    Escala.id_residente == id_residente,
                )
            )
            if conflito.first() is not None:
                log(rotulo, "vaga já ocupada -> rejeitando (rollback)")
                raise ConflitoDeEscalaError(
                    f"{rotulo}: residente {id_residente} já está escalado em "
                    f"{dia_semana}/{turno} na unidade {id_unidade}"
                )

            nova_escala = Escala(
                id_unidade=id_unidade,
                dia_semana=dia_semana,
                turno=turno,
                id_residente=id_residente,
                id_preceptor=id_preceptor,
            )
            session.add(nova_escala)
            await session.flush()
            log(rotulo, f"vaga livre -> INSERT ok (id_escala={nova_escala.id_escala}), commitando")

        log(rotulo, "commit efetivado, lock liberado")
        return nova_escala.id_escala


async def _limpar(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    id_unidade: int,
    dia_semana: str,
    turno: str,
    id_residente: int,
) -> None:
    """Remove a escala inserida pela demonstração, para que o script seja reexecutável
    sem deixar resíduo no banco (a UNIQUE rejeitaria uma segunda execução caso contrário)."""
    async with session_factory() as session:
        async with session.begin():
            await session.execute(
                delete(Escala).where(
                    Escala.id_unidade == id_unidade,
                    Escala.dia_semana == dia_semana,
                    Escala.turno == turno,
                    Escala.id_residente == id_residente,
                )
            )


async def executar_demonstracao(
    *,
    id_unidade: int,
    dia_semana: str,
    turno: str,
    id_residente: int,
    id_preceptor: int,
    limpar_ao_final: bool = True,
) -> tuple[bool, bool]:
    """Dispara as transações A e B concorrentemente e retorna (sucesso_a, sucesso_b).

    Reaproveitada tanto pelo `main()` (CLI) quanto pelo teste automatizado
    (`backend/tests/test_concorrencia.py`), que afirma que exatamente uma teve sucesso.
    """
    log("orquestrador", (
        f"disputando unidade={id_unidade} dia={dia_semana} turno={turno} "
        f"residente={id_residente}"
    ))

    tarefa_a = tentar_agendar_escala(
        async_session_factory,
        rotulo="Transação A",
        id_unidade=id_unidade,
        dia_semana=dia_semana,
        turno=turno,
        id_residente=id_residente,
        id_preceptor=id_preceptor,
        atraso_com_lock=2.0,
    )
    tarefa_b = tentar_agendar_escala(
        async_session_factory,
        rotulo="Transação B",
        id_unidade=id_unidade,
        dia_semana=dia_semana,
        turno=turno,
        id_residente=id_residente,
        id_preceptor=id_preceptor,
        atraso_inicial=0.3,
    )

    resultado_a, resultado_b = await asyncio.gather(tarefa_a, tarefa_b, return_exceptions=True)

    sucesso_a = not isinstance(resultado_a, Exception)
    sucesso_b = not isinstance(resultado_b, Exception)

    for rotulo, resultado, sucesso in (
        ("Transação A", resultado_a, sucesso_a),
        ("Transação B", resultado_b, sucesso_b),
    ):
        if sucesso:
            log(rotulo, f"RESULTADO FINAL: sucesso (id_escala={resultado})")
        else:
            log(rotulo, f"RESULTADO FINAL: rejeitada ({resultado})")

    if limpar_ao_final:
        await _limpar(
            async_session_factory,
            id_unidade=id_unidade,
            dia_semana=dia_semana,
            turno=turno,
            id_residente=id_residente,
        )
        log("orquestrador", "limpeza concluída (escala de demonstração removida)")

    return sucesso_a, sucesso_b


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Demonstra o lock pessimista contra a corrida de duas transações "
            "escalando o mesmo residente para o mesmo dia/turno/unidade."
        )
    )
    # Padrões: uma combinação livre no seed (db/05_seed.sql) — residente 15 (Jonas) não
    # tem nenhuma escala às quintas, em nenhuma unidade.
    parser.add_argument("--id-unidade", type=int, default=1)
    parser.add_argument("--dia-semana", default="QUI", choices=[
        "SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM",
    ])
    parser.add_argument("--turno", default="TARDE", choices=["MANHA", "TARDE", "NOITE"])
    parser.add_argument("--id-residente", type=int, default=15)
    parser.add_argument("--id-preceptor", type=int, default=6)
    parser.add_argument(
        "--manter-escala",
        action="store_true",
        help="Não remove a escala vencedora ao final (por padrão o script limpa após rodar).",
    )
    return parser.parse_args()


async def main() -> None:
    args = _parse_args()
    sucesso_a, sucesso_b = await executar_demonstracao(
        id_unidade=args.id_unidade,
        dia_semana=args.dia_semana,
        turno=args.turno,
        id_residente=args.id_residente,
        id_preceptor=args.id_preceptor,
        limpar_ao_final=not args.manter_escala,
    )

    total_sucessos = int(sucesso_a) + int(sucesso_b)
    print()
    print(f"Total de transações bem-sucedidas: {total_sucessos} (esperado: 1)")
    if total_sucessos != 1:
        raise SystemExit(
            "FALHA: o lock pessimista deveria garantir exatamente um vencedor."
        )


if __name__ == "__main__":
    asyncio.run(main())
