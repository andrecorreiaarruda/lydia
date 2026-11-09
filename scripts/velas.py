#!/usr/bin/env python3
"""Grava as velas diárias (abertura, máxima, mínima, fechamento e volume) de cada ativo em data/mercado.json.

Uso: python3 scripts/velas.py [pasta-do-repositório]

Fonte: brapi.dev, plano gratuito (1 ativo por chamada, velas diárias, até 3 meses por chamada).
O token não fica neste repositório: na sessão da tarefa agendada, o proxy de rede acrescenta o
cabeçalho de autorização. Fora dela, defina BRAPI_TOKEN no ambiente.

Junta com as velas que já estão no arquivo (a mais nova vence), guarda no máximo 250 por ativo e
não grava a vela de hoje antes das 18h30 de Brasília, quando o pregão ainda não fechou.
Não mexe em preco, var, hist nem em nenhum outro campo.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BRT = timezone(timedelta(hours=-3))
MAX_VELAS = 250


def buscar(ticker: str):
    url = f"https://brapi.dev/api/quote/{ticker}?range=3mo&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "lydia-painel/1.0"})
    token = os.environ.get("BRAPI_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    for tentativa in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                j = json.load(r)
            res = (j.get("results") or [None])[0]
            if not res:
                raise ValueError(j.get("message") or "resposta sem results")
            return res.get("historicalDataPrice") or []
        except urllib.error.HTTPError as e:
            corpo = e.read().decode("utf-8", "replace")[:200]
            if e.code in (429, 500, 502, 503, 504) and tentativa < 2:
                time.sleep(3 * (tentativa + 1))
                continue
            raise RuntimeError(f"HTTP {e.code}: {corpo}") from None
        except (urllib.error.URLError, TimeoutError) as e:
            if tentativa < 2:
                time.sleep(3 * (tentativa + 1))
                continue
            raise RuntimeError(str(e)) from None
    return []


def num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0


def main():
    raiz = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent)
    arq = raiz / "data" / "mercado.json"
    m = json.loads(arq.read_text(encoding="utf-8"))
    agora = datetime.now(BRT)
    hoje = agora.date().isoformat()
    pregao_fechado = (agora.hour, agora.minute) >= (18, 30)
    falhas = []
    for tk, a in m.get("ativos", {}).items():
        try:
            brutas = buscar(tk)
        except Exception as e:  # noqa: BLE001 — registra e segue para o próximo ativo
            falhas.append(f"{tk}: {e}")
            continue
        velas = {v["d"]: v for v in a.get("velas", []) if isinstance(v, dict) and "d" in v}
        novas = 0
        for x in brutas:
            o, h, l, c = x.get("open"), x.get("high"), x.get("low"), x.get("close")
            if not (num(o) and num(h) and num(l) and num(c)) or not isinstance(x.get("date"), (int, float)):
                continue
            d = datetime.fromtimestamp(x["date"], BRT).date().isoformat()
            if d == hoje and not pregao_fechado:
                continue
            vol = x.get("volume")
            velas[d] = {"d": d, "o": o, "h": max(h, o, c), "l": min(l, o, c), "c": c,
                        "v": int(vol) if isinstance(vol, (int, float)) and vol >= 0 else None}
            novas += 1
        a["velas"] = [velas[k] for k in sorted(velas)][-MAX_VELAS:]
        print(f"{tk}: {novas} velas da brapi, {len(a['velas'])} no arquivo (última {a['velas'][-1]['d'] if a['velas'] else '—'})")
        time.sleep(0.4)
    arq.write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if falhas:
        print("\nFalharam:", *falhas, sep="\n  ")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
