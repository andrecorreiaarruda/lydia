#!/usr/bin/env python3
"""Grava data/sessions.json: calendário de pregões da B3.

Uso: python3 scripts/sessoes.py [pasta-do-repositório]

Dias sem pregão: sábados, domingos, feriados nacionais (fixos e os que dependem da Páscoa:
Carnaval segunda e terça, Sexta-feira Santa e Corpus Christi), Consciência Negra (20/11, feriado
nacional desde 2024) e os dias 24/12 e 31/12, em que a B3 não abre.
O calendário oficial da B3 pode ter exceções; o campo "aviso" do arquivo diz isso.
"""
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

BRT = timezone(timedelta(hours=-3))


def pascoa(ano: int) -> date:
    # algoritmo de Meeus/Jones/Butcher (calendário gregoriano)
    a, b, c = ano % 19, ano // 100, ano % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = (h + l - 7 * m + 114) % 31 + 1
    return date(ano, mes, dia)


def feriados(ano: int) -> dict:
    p = pascoa(ano)
    f = {
        date(ano, 1, 1): "Confraternização Universal",
        p - timedelta(days=48): "Carnaval",
        p - timedelta(days=47): "Carnaval",
        p - timedelta(days=2): "Sexta-feira Santa",
        date(ano, 4, 21): "Tiradentes",
        date(ano, 5, 1): "Dia do Trabalho",
        p + timedelta(days=60): "Corpus Christi",
        date(ano, 9, 7): "Independência",
        date(ano, 10, 12): "Nossa Senhora Aparecida",
        date(ano, 11, 2): "Finados",
        date(ano, 11, 15): "Proclamação da República",
        date(ano, 11, 20): "Dia da Consciência Negra",
        date(ano, 12, 24): "Véspera de Natal (B3 fechada)",
        date(ano, 12, 25): "Natal",
        date(ano, 12, 31): "Último dia do ano (B3 fechada)",
    }
    return dict(sorted(f.items()))


def tem_pregao(d: date, fer: dict) -> bool:
    return d.weekday() < 5 and d not in fer


def main():
    raiz = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent)
    agora = datetime.now(BRT).replace(microsecond=0)
    hoje = agora.date()
    fer = {**feriados(hoje.year), **feriados(hoje.year + 1)}

    ultimo = hoje if tem_pregao(hoje, fer) else None
    d = hoje
    while ultimo is None:
        d -= timedelta(days=1)
        if tem_pregao(d, fer):
            ultimo = d
    proximos, d = [], hoje
    while len(proximos) < 10:
        d += timedelta(days=1)
        if tem_pregao(d, fer):
            proximos.append(d.isoformat())

    dados = {
        "atualizadoEm": agora.isoformat(),
        "hoje": hoje.isoformat(),
        "pregaoHoje": tem_pregao(hoje, fer),
        "motivoSemPregao": None if tem_pregao(hoje, fer) else (fer.get(hoje) or "fim de semana"),
        "ultimoPregao": ultimo.isoformat(),
        "proximosPregoes": proximos,
        "feriados": [{"d": k.isoformat(), "nome": v, "diaUtil": k.weekday() < 5}
                     for k, v in fer.items() if k >= hoje - timedelta(days=31)],
        "aviso": "Calendário calculado a partir dos feriados nacionais e das regras fixas da B3; confira o calendário oficial da B3 para exceções.",
    }
    arq = raiz / "data" / "sessions.json"
    arq.write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"pregão hoje: {dados['pregaoHoje']} · último: {dados['ultimoPregao']} · próximo: {proximos[0]}")


if __name__ == "__main__":
    main()
