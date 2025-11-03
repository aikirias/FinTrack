from decimal import Decimal, ROUND_HALF_UP

from app.schemas.exchange_rate import ExchangeRateValues

SUPPORTED_CURRENCIES = {"ARS", "USD", "BTC"}


def _quantize(value: Decimal, precision: str = "0.00000001") -> Decimal:
    return value.quantize(Decimal(precision), rounding=ROUND_HALF_UP)


def convert_amounts(
    amount: Decimal,
    currency_code: str,
    rates: ExchangeRateValues,
    rate_type: str = "official",
) -> tuple[Decimal, Decimal, Decimal]:
    currency_code = currency_code.upper()
    if currency_code not in SUPPORTED_CURRENCIES:
        raise ValueError(f"Moneda no soportada: {currency_code}")

    usd_rate = rates.usd_ars_oficial
    if rate_type == "blue" and rates.usd_ars_blue is not None:
        usd_rate = rates.usd_ars_blue

    amount_ars: Decimal
    amount_usd: Decimal
    amount_btc: Decimal

    if currency_code == "ARS":
        amount_ars = amount
        amount_usd = amount / usd_rate
        amount_btc = amount / rates.btc_ars
    elif currency_code == "USD":
        amount_usd = amount
        amount_ars = amount * usd_rate
        amount_btc = amount / rates.btc_usd
    else:  # BTC
        amount_btc = amount
        amount_usd = amount * rates.btc_usd
        amount_ars = amount * rates.btc_ars

    return (
        _quantize(amount_ars),
        _quantize(amount_usd),
        _quantize(amount_btc),
    )
