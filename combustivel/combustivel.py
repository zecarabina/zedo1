#!/usr/bin/env python3
"""Administrador de combustível do carro.

Uso:
  python3 combustivel.py add LITROS VALOR KM --carro yaris [--data AAAA-MM-DD]
  python3 combustivel.py prever KM_ATUAL --carro yaris [--preco 3.99]
  python3 combustivel.py resumo [--carro yaris]

Premissa: cada abastecimento enche o tanque. O consumo (km/L) de um
trecho = km rodados desde o abastecimento anterior / litros do abastecimento atual.
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

ARQUIVO = Path(__file__).with_name("abastecimentos.json")
PRECO_PADRAO = 3.99


def carregar():
    if ARQUIVO.exists():
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    return []


def salvar(registros):
    ARQUIVO.write_text(json.dumps(registros, indent=2, ensure_ascii=False), encoding="utf-8")


def brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def trechos(registros):
    """Retorna (km, litros) entre abastecimentos consecutivos."""
    r = sorted(registros, key=lambda x: x["km"])
    return [(b["km"] - a["km"], b["litros"]) for a, b in zip(r, r[1:]) if b["km"] > a["km"]]


def consumo_medio(registros):
    t = trechos(registros)
    litros = sum(l for _, l in t)
    return sum(k for k, _ in t) / litros if litros else None


def do_carro(todos, carro):
    """Registros de um carro (registros antigos sem 'carro' são do yaris)."""
    return [r for r in todos if r.get("carro", "yaris") == carro]


def cmd_add(args):
    todos = carregar()
    reg = do_carro(todos, args.carro)
    if reg and args.km <= max(r["km"] for r in reg):
        sys.exit("Erro: a quilometragem precisa ser maior que a do último abastecimento.")
    preco = args.valor / args.litros
    reg.append({"carro": args.carro, "data": args.data, "litros": args.litros, "valor": args.valor,
                "km": args.km, "preco_litro": round(preco, 3)})
    salvar(todos + [reg[-1]])
    print(f"[{args.carro}] Registrado: {args.litros:.2f} L, {brl(args.valor)} ({brl(preco)}/L), {args.km:.0f} km")
    if len(reg) > 1:
        a, b = sorted(reg, key=lambda x: x["km"])[-2:]
        print(f"Neste trecho: {(b['km']-a['km'])/b['litros']:.2f} km/L "
              f"| média geral: {consumo_medio(reg):.2f} km/L")


def cmd_prever(args):
    reg = do_carro(carregar(), args.carro)
    media = consumo_medio(reg)
    if media is None:
        sys.exit("Preciso de pelo menos 2 abastecimentos para calcular o consumo.")
    ultimo = max(reg, key=lambda x: x["km"])
    rodados = args.km_atual - ultimo["km"]
    if rodados <= 0:
        sys.exit("Erro: km atual precisa ser maior que o do último abastecimento.")
    litros = rodados / media
    print(f"Rodou {rodados:.0f} km desde o último abastecimento")
    print(f"Consumo médio: {media:.2f} km/L")
    print(f"Litros estimados: {litros:.2f} L")
    print(f"Você deve gastar: {brl(litros * args.preco)} (a {brl(args.preco)}/L)")


def cmd_resumo(args):
    todos = carregar()
    carros = [args.carro] if args.carro else sorted({r.get("carro", "yaris") for r in todos})
    if not carros:
        sys.exit("Nenhum abastecimento registrado.")
    for c in carros:
        print(f"=== {c} ===")
        resumo_carro(do_carro(todos, c))
        print()


def resumo_carro(reg):
    reg = sorted(reg, key=lambda x: x["km"])
    if not reg:
        print("Nenhum abastecimento registrado.")
        return
    for r in reg:
        print(f"{r['data']}  {r['km']:>8.0f} km  {r['litros']:>6.2f} L  {brl(r['valor']):>11}  {brl(r['preco_litro'])}/L")
    print(f"\nTotal gasto: {brl(sum(r['valor'] for r in reg))}")
    media = consumo_medio(reg)
    if media:
        km = sum(k for k, _ in trechos(reg))
        custo_km = sum(r["valor"] for r in reg[1:]) / km
        print(f"Consumo médio: {media:.2f} km/L | custo por km: {brl(custo_km)}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    a = s.add_parser("add")
    a.add_argument("litros", type=float)
    a.add_argument("valor", type=float)
    a.add_argument("km", type=float)
    a.add_argument("--carro", required=True, help="ex.: yaris, tcross")
    a.add_argument("--data", default=date.today().isoformat())
    a.set_defaults(f=cmd_add)
    v = s.add_parser("prever")
    v.add_argument("km_atual", type=float)
    v.add_argument("--carro", required=True)
    v.add_argument("--preco", type=float, default=PRECO_PADRAO)
    v.set_defaults(f=cmd_prever)
    r = s.add_parser("resumo")
    r.add_argument("--carro")
    r.set_defaults(f=cmd_resumo)
    args = p.parse_args()
    args.f(args)


if __name__ == "__main__":
    main()
