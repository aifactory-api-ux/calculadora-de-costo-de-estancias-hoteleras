"""Cálculo del costo de las estadías de un hotel.

La librería expone funciones puras que concentran las reglas de precio del
hotel para que el equipo de revenue no tenga que reimplementarlas en cada
script:

- `nights(check_in, check_out)`: duración de la estadía en noches.
- `nightly_rate(day, room)`: tarifa de la noche que comienza en un día.
- `stay_total(check_in, check_out, room, guests)`: total de la estadía, con
  descuento por estadía larga y tasa turística.

Los importes monetarios se calculan con `decimal.Decimal` y la aritmética es
exacta: nunca se usan números de coma flotante para dinero.

La distribución `hotel-booking` publica este módulo con el nombre `booking`,
de modo que se importa sin el prefijo del directorio:

    from booking import nights, nightly_rate, stay_total
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import cast

__all__ = ["nights", "nightly_rate", "stay_total"]

# Duración máxima admitida por estadía, en noches.
_MAX_NIGHTS = 30

# Tarifa base por noche y tipo de habitación.
_BASE_RATES: dict[str, Decimal] = {
    "single": Decimal("50.00"),
    "double": Decimal("80.00"),
    "suite": Decimal("150.00"),
}

# Número máximo de huéspedes admitido por tipo de habitación.
_CAPACITY: dict[str, int] = {
    "single": 1,
    "double": 2,
    "suite": 4,
}

# Multiplicador del recargo aplicado a la tarifa base en las noches de fin
# de semana (viernes y sábado): 1.25 equivale a un recargo del 25 %.
_WEEKEND_MULTIPLIER = Decimal("1.25")

# Días de la semana con recargo: viernes (4) y sábado (5).
_SURCHARGE_WEEKDAYS = (4, 5)

# Tasa turística aplicada por huésped y por noche.
_TAX_PER_GUEST_PER_NIGHT = Decimal("2.50")

# Número de noches a partir del cual se aplica el descuento por estadía larga.
_LONG_STAY_MIN_NIGHTS = 7

# Multiplicador del descuento por estadía larga: 0.90 equivale a un 10 % de
# descuento sobre el subtotal de habitación.
_LONG_STAY_MULTIPLIER = Decimal("0.90")

# Precisión monetaria: todos los importes se cuantizan a dos decimales.
_MONEY_QUANTUM = Decimal("0.01")


def _require_date(value: object, name: str) -> date:
    """Comprueba que `value` sea una `datetime.date` y la devuelve.

    `datetime.datetime` hereda de `datetime.date`, por lo que se descarta de
    forma explícita: la hora no tiene sentido en una fecha de check-in o de
    check-out y aceptarla ocultaría el error de quien llama.

    Args:
        value: Valor a validar.
        name: Nombre del argumento, usado en el mensaje de error.

    Returns:
        El mismo valor, garantizado como `datetime.date`.

    Raises:
        TypeError: Si `value` no es una `datetime.date` o es una
            `datetime.datetime`.
    """
    if isinstance(value, datetime):
        raise TypeError(
            f"{name} debe ser datetime.date, no datetime.datetime: {value!r}"
        )
    if not isinstance(value, date):
        raise TypeError(f"{name} debe ser datetime.date: {type(value).__name__}")
    return cast(date, value)


def _require_room(room: object) -> str:
    """Comprueba que `room` sea un tipo de habitación conocido y lo devuelve.

    Los nombres de habitación son exactos y sensibles a mayúsculas: `"Double"`
    no es una habitación válida.

    Args:
        room: Valor a validar.

    Returns:
        El mismo valor, garantizado como nombre de habitación válido.

    Raises:
        ValueError: Si `room` no es uno de `single`, `double` o `suite`.
    """
    if not isinstance(room, str) or room not in _BASE_RATES:
        raise ValueError(
            f"habitación desconocida: {room!r} "
            f"(disponibles: {', '.join(sorted(_BASE_RATES))})"
        )
    return room


def nights(check_in: date, check_out: date) -> int:
    """Devuelve el número de noches de la estadía.

    La estadía incluye la noche que comienza en `check_in` y excluye la noche
    que comienza en `check_out`.

    Args:
        check_in: Fecha de entrada, como `datetime.date`.
        check_out: Fecha de salida, como `datetime.date`.

    Returns:
        El número entero de noches de la estadía.

    Raises:
        TypeError: Si `check_in` o `check_out` no son `datetime.date` o son
            `datetime.datetime`.
        ValueError: Si `check_out` no es posterior a `check_in` o si la
            estadía supera las 30 noches.

    Examples:
        >>> nights(date(2026, 1, 2), date(2026, 1, 4))
        2
    """
    _require_date(check_in, "check_in")
    _require_date(check_out, "check_out")

    if check_out <= check_in:
        raise ValueError(
            "check_out debe ser posterior a check_in "
            f"(check_in={check_in.isoformat()}, check_out={check_out.isoformat()})"
        )

    total = (check_out - check_in).days
    if total > _MAX_NIGHTS:
        raise ValueError(
            f"la estadía no puede superar {_MAX_NIGHTS} noches (recibidas: {total})"
        )

    return total


def nightly_rate(day: date, room: str) -> Decimal:
    """Devuelve la tarifa de la noche que comienza en `day` para `room`.

    La tarifa base depende del tipo de habitación (`single` 50.00, `double`
    80.00 y `suite` 150.00) y las noches que comienzan en viernes o en sábado
    llevan un recargo del 25 % sobre esa base.

    El recargo se aplica a la noche que *comienza* en el día indicado: la
    noche del viernes es la del viernes al sábado y la del sábado es la del
    sábado al domingo.

    Args:
        day: Fecha en la que comienza la noche, como `datetime.date`.
        room: Tipo de habitación: `single`, `double` o `suite`.

    Returns:
        La tarifa de la noche como `Decimal` con exactamente dos decimales,
        redondeada con `ROUND_HALF_UP`.

    Raises:
        TypeError: Si `day` no es una `datetime.date` o es una
            `datetime.datetime`.
        ValueError: Si `room` no es uno de `single`, `double` o `suite`.

    Examples:
        >>> nightly_rate(date(2026, 1, 5), "double")
        Decimal('80.00')
        >>> nightly_rate(date(2026, 1, 2), "double")
        Decimal('100.00')
    """
    _require_date(day, "day")
    room = _require_room(room)

    rate = _BASE_RATES[room]
    if day.weekday() in _SURCHARGE_WEEKDAYS:
        rate = rate * _WEEKEND_MULTIPLIER

    return rate.quantize(_MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def stay_total(check_in: date, check_out: date, room: str, guests: int) -> Decimal:
    """Devuelve el total de la estadía: habitación y tasa turística.

    El total es la suma de la tarifa de cada noche de la estadía (desde la
    noche que comienza en `check_in` hasta la noche que comienza el día
    anterior a `check_out`) más una tasa turística de 2.50 por huésped y por
    noche.

    Las estadías de 7 noches o más reciben un descuento del 10 % que se aplica
    únicamente sobre el subtotal de habitación: la tasa turística se suma
    después, sin descontar.

    Args:
        check_in: Fecha de entrada, como `datetime.date`.
        check_out: Fecha de salida, como `datetime.date`.
        room: Tipo de habitación: `single`, `double` o `suite`.
        guests: Número de huéspedes, entre 1 y la capacidad de la habitación.

    Returns:
        El total de la estadía como `Decimal` con exactamente dos decimales,
        redondeado con `ROUND_HALF_UP`.

    Raises:
        TypeError: Si `check_in` o `check_out` no son `datetime.date` o son
            `datetime.datetime`, o si `guests` no es un `int` (un `bool` no
            se admite).
        ValueError: Si `check_out` no es posterior a `check_in`, si la
            estadía supera las 30 noches, si `room` no es un tipo de
            habitación conocido o si `guests` está fuera del rango de 1 a la
            capacidad de la habitación.

    Examples:
        >>> stay_total(date(2026, 1, 2), date(2026, 1, 4), "double", 2)
        Decimal('210.00')
    """
    total_nights = nights(check_in, check_out)
    room = _require_room(room)
    capacity = _CAPACITY[room]

    if isinstance(guests, bool) or not isinstance(guests, int):
        raise TypeError(f"guests debe ser int, no {type(guests).__name__}: {guests!r}")
    if not 1 <= guests <= capacity:
        raise ValueError(
            f"guests debe estar entre 1 y la capacidad de la habitación "
            f"'{room}' ({capacity}), recibido: {guests}"
        )

    subtotal = sum(
        (
            nightly_rate(check_in + timedelta(days=indice), room)
            for indice in range(total_nights)
        ),
        Decimal("0.00"),
    )
    if total_nights >= _LONG_STAY_MIN_NIGHTS:
        subtotal = (subtotal * _LONG_STAY_MULTIPLIER).quantize(
            _MONEY_QUANTUM, rounding=ROUND_HALF_UP
        )

    tax = guests * _TAX_PER_GUEST_PER_NIGHT * total_nights

    return (subtotal + tax).quantize(_MONEY_QUANTUM, rounding=ROUND_HALF_UP)
