from decimal import Decimal, ROUND_HALF_UP

from app.schemas.exchange_rate import ExchangeRateValues

SUPPORTED_CURRENCIES = {"ARS", "USD", "BTC"}

CURRENCY_PRECISION = {
    "ARS": "0.01",
    "USD": "0.01",
    "BTC": "0.00000001",
}


def _quantize(value: Decimal, currency: str = "BTC") -> Decimal:
    precision = CURRENCY_PRECISION.get(currency.upper(), "0.00000001")
    return value.quantize(Decimal(precision), rounding=ROUND_HALF_UP)


def _validate_rates(rates: ExchangeRateValues, usd_rate: Decimal) -> None:
    if usd_rate <= 0:
        raise ValueError("Tasa USD/ARS inválida o igual a cero")
    if rates.btc_ars <= 0:
        raise ValueError("Tasa BTC/ARS inválida o igual a cero")
    if rates.btc_usd <= 0:
        raise ValueError("Tasa BTC/USD inválida o igual a cero")


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

    _validate_rates(rates, usd_rate)

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
        _quantize(amount_ars, "ARS"),
        _quantize(amount_usd, "USD"),
        _quantize(amount_btc, "BTC"),
    )
