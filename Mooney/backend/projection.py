"""
Mooney - Projecao de investimentos.

Responde: "quanto vou ter em X data?" e "e se eu aportar Y por dia/mes/em uma data?"

Como funciona:
  * Cada aporte vira um "lote" que rende juros compostos desde a sua data.
  * O IR regressivo e calculado POR LOTE (cada aporte tem sua propria idade).
  * Taxa anual efetiva -> taxa diaria: (1 + a) ** (1/365) - 1  (dias corridos).

Aviso: e uma ESTIMATIVA. Usa dias corridos (nao dias uteis), nao considera IOF,
come-cotas de fundos, nem variacao futura de CDI/Selic/IPCA.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Literal, Optional

Frequency = Literal["once", "daily", "weekly", "monthly", "yearly"]
RateType = Literal["prefixed", "cdi_percent", "selic", "ipca_plus", "savings", "variable"]
TaxRegime = Literal["ir_regressive", "exempt", "none"]


@dataclass
class Contribution:
    amount: float
    frequency: Frequency
    starts_on: date
    ends_on: Optional[date] = None  # None = ate a data-alvo


def effective_annual_rate(
    rate_type: RateType,
    rate_value: float,
    cdi: Optional[float] = None,    # % a.a., ex: 14.9
    selic: Optional[float] = None,  # % a.a.
    ipca: Optional[float] = None,   # % a.a. esperado
) -> float:
    """Converte a configuracao do investimento em taxa anual efetiva (0.12 = 12% a.a.)."""
    if rate_type in ("prefixed", "variable"):
        return rate_value / 100
    if rate_type == "cdi_percent":
        if cdi is None:
            raise ValueError("Informe o CDI para investimentos '% do CDI'.")
        return (cdi / 100) * (rate_value / 100)
    if rate_type == "selic":
        if selic is None:
            raise ValueError("Informe a Selic.")
        return (selic + rate_value) / 100
    if rate_type == "ipca_plus":
        if ipca is None:
            raise ValueError("Informe o IPCA esperado.")
        return (1 + ipca / 100) * (1 + rate_value / 100) - 1
    if rate_type == "savings":
        if selic is None:
            raise ValueError("Informe a Selic.")
        # Regra da poupanca: Selic > 8,5% -> 0,5% a.m.; senao 70% da Selic (TR ~ 0)
        return (1.005 ** 12 - 1) if selic > 8.5 else 0.7 * selic / 100
    raise ValueError(f"rate_type desconhecido: {rate_type}")


def daily_rate(annual_rate: float) -> float:
    return (1 + annual_rate) ** (1 / 365) - 1


def ir_regressive_rate(days: int) -> float:
    """Tabela regressiva do IR sobre renda fixa."""
    if days <= 180:
        return 0.225
    if days <= 360:
        return 0.20
    if days <= 720:
        return 0.175
    return 0.15


def _add_months(d: date, months: int, anchor_day: int) -> date:
    y, m = divmod(d.year * 12 + (d.month - 1) + months, 12)
    m += 1
    return date(y, m, min(anchor_day, calendar.monthrange(y, m)[1]))


def expand_contribution(c: Contribution, end: date) -> Iterable[tuple[date, float]]:
    """Transforma uma regra de aporte em datas concretas."""
    last = min(c.ends_on, end) if c.ends_on else end
    if c.starts_on > last:
        return
    if c.frequency == "once":
        yield c.starts_on, c.amount
    elif c.frequency == "daily":
        d = c.starts_on
        while d <= last:
            yield d, c.amount
            d += timedelta(days=1)
    elif c.frequency == "weekly":
        d = c.starts_on
        while d <= last:
            yield d, c.amount
            d += timedelta(days=7)
    elif c.frequency == "monthly":
        i = 0
        while (d := _add_months(c.starts_on, i, c.starts_on.day)) <= last:
            yield d, c.amount
            i += 1
    elif c.frequency == "yearly":
        i = 0
        while (d := _add_months(c.starts_on, 12 * i, c.starts_on.day)) <= last:
            yield d, c.amount
            i += 1


def _money(x: float) -> float:
    return float(Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def project(
    initial_amount: float,
    start_date: date,
    end_date: date,
    annual_rate: float,                       # efetiva, ex: 0.12
    contributions: Optional[list[Contribution]] = None,
    tax_regime: TaxRegime = "ir_regressive",
) -> dict:
    """
    Projeta o patrimonio ate end_date.
    O 'initial_amount' e tratado como um lote que comecou em start_date.
    (Se o saldo atual ja tem rendimento embutido, o IR sera estimado a partir de start_date.)
    """
    if end_date < start_date:
        raise ValueError("A data-alvo precisa ser depois da data inicial.")

    dr = daily_rate(annual_rate)

    lots: list[tuple[date, float]] = []
    if initial_amount > 0:
        lots.append((start_date, initial_amount))
    for c in contributions or []:
        lots.extend(expand_contribution(c, end_date))
    lots.sort(key=lambda x: x[0])

    def gross_at(day: date) -> tuple[float, float]:
        invested = value = 0.0
        for d, amt in lots:
            if d > day:
                break
            invested += amt
            value += amt * (1 + dr) ** (day - d).days
        return invested, value

    # Linha do tempo: ultimo dia de cada mes + data final
    timeline = []
    cursor = date(start_date.year, start_date.month, 1)
    points = []
    while cursor <= end_date:
        eom = date(cursor.year, cursor.month, calendar.monthrange(cursor.year, cursor.month)[1])
        points.append(min(eom, end_date))
        cursor = _add_months(cursor, 1, 1)
    if points[-1] != end_date:
        points.append(end_date)
    for p in points:
        inv, val = gross_at(p)
        timeline.append({"date": p.isoformat(), "invested": _money(inv), "gross_value": _money(val)})

    # Resultado final com IR por lote
    invested = gross = tax = 0.0
    for d, amt in lots:
        days = (end_date - d).days
        lot_value = amt * (1 + dr) ** days
        lot_gain = lot_value - amt
        invested += amt
        gross += lot_value
        if tax_regime == "ir_regressive" and lot_gain > 0:
            tax += lot_gain * ir_regressive_rate(days)

    gross_gain = gross - invested
    return {
        "invested": _money(invested),
        "gross_value": _money(gross),
        "gross_gain": _money(gross_gain),
        "estimated_tax": _money(tax),
        "net_value": _money(gross - tax),
        "net_gain": _money(gross_gain - tax),
        "annual_rate_used": annual_rate,
        "timeline": timeline,
    }


def compare_scenarios(
    initial_amount: float,
    start_date: date,
    end_date: date,
    annual_rate: float,
    extra: list[Contribution],
    tax_regime: TaxRegime = "ir_regressive",
) -> dict:
    """Cenario base (sem aportes) x cenario com aportes extras. Pronto para o grafico do React."""
    base = project(initial_amount, start_date, end_date, annual_rate, [], tax_regime)
    with_extra = project(initial_amount, start_date, end_date, annual_rate, extra, tax_regime)
    return {
        "base": base,
        "with_extra": with_extra,
        "difference_net": _money(with_extra["net_value"] - base["net_value"]),
        "extra_invested": _money(with_extra["invested"] - base["invested"]),
        "extra_net_gain": _money(with_extra["net_gain"] - base["net_gain"]),
    }


if __name__ == "__main__":
    # Exemplo de teste:
    rate = effective_annual_rate("cdi_percent", 110, cdi=14.9)
    start, end = date(2026, 10, 11), date(2029, 1, 1)

    result = compare_scenarios(
        initial_amount=10_000,
        start_date=start,
        end_date=end,
        annual_rate=rate,
        extra=[
            Contribution(500, "monthly", date(2026, 11, 5)),
            Contribution(3_000, "once", date(2027, 12, 20)),
        ],
    )
    print(f"Taxa efetiva: {rate:.2%} a.a.")
    for k in ("base", "with_extra"):
        r = result[k]
        print(f"\n[{k}] investido R$ {r['invested']:,.2f} | bruto R$ {r['gross_value']:,.2f} "
              f"| IR R$ {r['estimated_tax']:,.2f} | liquido R$ {r['net_value']:,.2f}")
    print(f"\nGanho liquido extra com os aportes: R$ {result['extra_net_gain']:,.2f}")
