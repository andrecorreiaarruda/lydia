#!/usr/bin/env python3
"""Confere data/mercado.json e data/noticias.json antes do commit.

Uso: python3 scripts/validar.py [pasta-do-repositório]
Sai com código 1 e lista os problemas quando algo está fora do formato que a página espera.
Avisos (⚠) não bloqueiam.
"""
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

TICKERS = {
    "BBAS3", "BBSE3", "BPAC11", "CXSE3", "ITUB4", "VALE3",
    "KNCR11", "KNSC11", "KNRI11", "HGLG11", "XPLG11", "PVBI11", "RBRP11",
    "QQQM", "NASD11",
}
INDICADORES = ("selic", "cdi", "ipca12m", "usdbrl", "ibov", "ust10")
DIA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MES = re.compile(r"^\d{4}-\d{2}$")

erros: list[str] = []
avisos: list[str] = []


def erro(msg):
    erros.append(msg)


def num(v, nulo=True):
    return (v is None and nulo) or (isinstance(v, (int, float)) and not isinstance(v, bool))


def texto(v, nulo=False):
    return (v is None and nulo) or (isinstance(v, str) and v.strip() != "")


def dia(v, nulo=True):
    if v is None:
        return nulo
    if not (isinstance(v, str) and DIA.match(v)):
        return False
    try:
        date.fromisoformat(v)
        return True
    except ValueError:
        return False


def url(v, nulo=True):
    return (v is None and nulo) or (isinstance(v, str) and v.startswith("https://"))


def ler(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        erro(f"{p.name}: arquivo não existe")
    except json.JSONDecodeError as e:
        erro(f"{p.name}: JSON inválido ({e})")
    return None


def conferir_mercado(m):
    if not isinstance(m, dict):
        return erro("mercado.json: precisa ser um objeto")
    if not dia(m.get("fechamento"), nulo=False):
        erro("mercado.fechamento: data AAAA-MM-DD obrigatória")
    if not texto(m.get("atualizadoEm")):
        erro("mercado.atualizadoEm: obrigatório (ISO com -03:00)")

    ind = m.get("indicadores")
    if not isinstance(ind, dict):
        erro("mercado.indicadores: precisa ser um objeto")
        ind = {}
    for k in INDICADORES:
        x = ind.get(k)
        if not isinstance(x, dict):
            erro(f"indicadores.{k}: falta")
            continue
        if not num(x.get("valor")):
            erro(f"indicadores.{k}.valor: precisa ser número ou null")
        if "var" in x and not num(x.get("var")):
            erro(f"indicadores.{k}.var: precisa ser número ou null")
        d = x.get("data")
        if not (d is None or dia(d) or (k == "ipca12m" and isinstance(d, str) and MES.match(d))):
            erro(f"indicadores.{k}.data: formato inválido ({d!r})")
        if not url(x.get("url")):
            erro(f"indicadores.{k}.url: precisa começar com https://")

    t = m.get("tesouro")
    if not isinstance(t, dict):
        erro("mercado.tesouro: precisa ser um objeto")
    else:
        if not dia(t.get("data")):
            erro("tesouro.data: formato inválido")
        if not url(t.get("url")):
            erro("tesouro.url: precisa começar com https://")
        tit = t.get("titulos")
        if not isinstance(tit, list) or not tit:
            erro("tesouro.titulos: lista obrigatória")
        else:
            for i, x in enumerate(tit):
                if not isinstance(x, dict) or not texto(x.get("nome")):
                    erro(f"tesouro.titulos[{i}].nome: obrigatório")
                    continue
                if x.get("tipo") not in ("selic", "selic100", "pre", "ipca"):
                    erro(f"tesouro.titulos[{i}].tipo: selic, selic100, pre ou ipca")
                if not num(x.get("taxa"), nulo=False):
                    erro(f"tesouro.titulos[{i}].taxa: número obrigatório")

    at = m.get("ativos")
    if not isinstance(at, dict):
        return erro("mercado.ativos: precisa ser um objeto")
    faltam = TICKERS - set(at)
    if faltam:
        avisos.append(f"ativos sem dados: {', '.join(sorted(faltam))}")
    for tk, a in at.items():
        if tk not in TICKERS:
            avisos.append(f"ativos.{tk}: não está na lista da página (será ignorado)")
        if not isinstance(a, dict):
            erro(f"ativos.{tk}: precisa ser um objeto")
            continue
        if not num(a.get("preco")) or (a.get("preco") is not None and a["preco"] <= 0):
            erro(f"ativos.{tk}.preco: número positivo ou null")
        for k in ("var", "dy", "pvp", "pl"):
            if k in a and not num(a.get(k)):
                erro(f"ativos.{tk}.{k}: número ou null")
        if not dia(a.get("data")):
            erro(f"ativos.{tk}.data: AAAA-MM-DD ou null")
        if a.get("data") is None and a.get("preco") is not None and not texto(a.get("obs")):
            avisos.append(f"ativos.{tk}: preço sem data e sem obs explicando")
        if "obs" in a and not texto(a.get("obs"), nulo=True):
            erro(f"ativos.{tk}.obs: texto")
        if not url(a.get("url")):
            erro(f"ativos.{tk}.url: precisa começar com https://")
        ur = a.get("ultimoRend")
        if ur is not None:
            if not isinstance(ur, dict) or not num(ur.get("valor")):
                erro(f"ativos.{tk}.ultimoRend: {{valor, dataCom, pagamento}}")
            else:
                for k in ("dataCom", "pagamento"):
                    if not dia(ur.get(k)):
                        erro(f"ativos.{tk}.ultimoRend.{k}: AAAA-MM-DD ou null")
        vs = a.get("velas", [])
        if not isinstance(vs, list):
            erro(f"ativos.{tk}.velas: lista")
        else:
            if len(vs) > 250:
                erro(f"ativos.{tk}.velas: no máximo 250 (tem {len(vs)})")
            anterior = ""
            for i, v in enumerate(vs):
                ok = isinstance(v, dict) and dia(v.get("d"), nulo=False) and all(num(v.get(k), nulo=False) and v[k] > 0 for k in ("o", "h", "l", "c"))
                if not ok:
                    erro(f"ativos.{tk}.velas[{i}]: {{\"d\", \"o\", \"h\", \"l\", \"c\", \"v\"}} com preços positivos")
                    break
                if v["l"] > min(v["o"], v["c"]) or v["h"] < max(v["o"], v["c"]):
                    erro(f"ativos.{tk}.velas[{i}] ({v['d']}): mínima/máxima não cobrem abertura e fechamento")
                    break
                if "v" in v and v["v"] is not None and not (num(v["v"], nulo=False) and v["v"] >= 0):
                    erro(f"ativos.{tk}.velas[{i}].v: volume ≥ 0 ou null")
                    break
                if v["d"] <= anterior:
                    erro(f"ativos.{tk}.velas: datas fora de ordem ou repetidas em {v['d']}")
                    break
                anterior = v["d"]
        h = a.get("hist", [])
        if not isinstance(h, list):
            erro(f"ativos.{tk}.hist: lista")
            continue
        if len(h) > 60:
            erro(f"ativos.{tk}.hist: no máximo 60 pontos (tem {len(h)})")
        anterior = ""
        for i, p in enumerate(h):
            if not isinstance(p, dict) or not dia(p.get("d"), nulo=False) or not num(p.get("p"), nulo=False) or p["p"] <= 0:
                erro(f"ativos.{tk}.hist[{i}]: {{\"d\": \"AAAA-MM-DD\", \"p\": preço}}")
                break
            if p["d"] <= anterior:
                erro(f"ativos.{tk}.hist: datas fora de ordem ou repetidas em {p['d']}")
                break
            anterior = p["d"]


def conferir_noticias(n):
    if not isinstance(n, dict):
        return erro("noticias.json: precisa ser um objeto")
    if not texto(n.get("atualizadoEm")):
        erro("noticias.atualizadoEm: obrigatório")
    itens = n.get("itens")
    if not isinstance(itens, list):
        return erro("noticias.itens: lista obrigatória")
    if len(itens) > 25:
        erro(f"noticias.itens: no máximo 25 (tem {len(itens)})")
    ref = str(n.get("atualizadoEm", ""))[:10]
    limite = None
    if dia(ref, nulo=False):
        limite = (date.fromisoformat(ref) - timedelta(days=7)).isoformat()
    vistos, anterior = set(), "9999-99-99"
    for i, x in enumerate(itens):
        nome = f"itens[{i}]"
        if not isinstance(x, dict):
            erro(f"{nome}: precisa ser um objeto")
            continue
        nome = f"itens[{i}] ({x.get('id')})"
        if not texto(x.get("id")):
            erro(f"{nome}.id: obrigatório")
        elif x["id"] in vistos:
            erro(f"{nome}.id: repetido")
        vistos.add(x.get("id"))
        d = x.get("data")
        if not dia(d, nulo=False):
            erro(f"{nome}.data: AAAA-MM-DD obrigatória")
        else:
            if d > anterior:
                erro(f"{nome}: fora de ordem (da mais nova para a mais antiga)")
            anterior = d
            if limite and d < limite:
                avisos.append(f"{nome}: mais de 7 dias, deveria ter saído")
        if x.get("tema") not in ("carteira", "macro", "politica"):
            erro(f"{nome}.tema: carteira, macro ou politica")
        for k in ("titulo", "resumo", "fonte"):
            if not texto(x.get(k)):
                erro(f"{nome}.{k}: obrigatório")
        if not url(x.get("url"), nulo=False):
            erro(f"{nome}.url: obrigatória, começando com https://")
        av = x.get("ativos", [])
        if not isinstance(av, list) or any(t not in TICKERS for t in av):
            erro(f"{nome}.ativos: lista com tickers da carteira")
        if x.get("tipo") not in ("fato", "opiniao", "rumor"):
            erro(f"{nome}.tipo: fato, opiniao ou rumor")
        if x.get("tese") not in ("nao", "observar", "risco"):
            erro(f"{nome}.tese: nao, observar ou risco")
        if not isinstance(x.get("confirma"), bool):
            erro(f"{nome}.confirma: true ou false")
        elif x["confirma"] and not texto(x.get("contraponto")):
            erro(f"{nome}.contraponto: obrigatório quando confirma é true")
        le = x.get("leituras")
        if x.get("tema") == "politica" or le is not None:
            if not isinstance(le, list) or len(le) != 2 or not all(isinstance(y, dict) and texto(y.get("quem")) and texto(y.get("diz")) for y in le):
                erro(f"{nome}.leituras: dois lados [{{quem, diz}}, {{quem, diz}}]")


def main():
    raiz = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent)
    m = ler(raiz / "data" / "mercado.json")
    n = ler(raiz / "data" / "noticias.json")
    if m is not None:
        conferir_mercado(m)
    if n is not None:
        conferir_noticias(n)
    for a in avisos:
        print("⚠", a)
    if erros:
        for e in erros:
            print("✗", e)
        print(f"\n{len(erros)} problema(s). Corrija antes do commit.")
        return 1
    print("OK: mercado.json e noticias.json no formato da página.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
