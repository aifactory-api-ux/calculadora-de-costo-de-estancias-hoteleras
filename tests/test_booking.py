"""Pruebas de la duración de la estadía (`nights`), de la tarifa por noche
(`nightly_rate`) y del total de la estadía (`stay_total`).

La suite se ejecuta desde la raíz del repositorio con:

    python -m pytest tests/test_booking.py
"""

from datetime import date, datetime
from decimal import Decimal

import pytest

from booking import nightly_rate, nights, stay_total


class TestNights:
    """Casos de cálculo de la duración de la estadía."""

    def test_una_noche(self):
        assert nights(date(2026, 1, 2), date(2026, 1, 3)) == 1

    def test_dos_noches(self):
        assert nights(date(2026, 1, 2), date(2026, 1, 4)) == 2

    def test_el_resultado_es_un_entero(self):
        resultado = nights(date(2026, 1, 2), date(2026, 1, 4))

        assert isinstance(resultado, int)
        assert not isinstance(resultado, bool)

    def test_limite_de_30_noches(self):
        assert nights(date(2026, 1, 1), date(2026, 1, 31)) == 30

    def test_31_noches_superan_el_limite(self):
        with pytest.raises(ValueError):
            nights(date(2026, 1, 1), date(2026, 2, 1))


class TestNightsErroresDeOrden:
    """Casos de `check_out` no posterior a `check_in`."""

    def test_check_out_anterior_al_check_in(self):
        with pytest.raises(ValueError):
            nights(date(2026, 1, 10), date(2026, 1, 5))

    def test_check_out_igual_al_check_in(self):
        with pytest.raises(ValueError):
            nights(date(2026, 1, 10), date(2026, 1, 10))


class TestNightsErroresDeTipo:
    """Casos de fechas que no son `datetime.date`."""

    @pytest.mark.parametrize(
        ("check_in", "check_out"),
        [
            (datetime(2026, 1, 2, 15, 30), date(2026, 1, 4)),
            (date(2026, 1, 2), datetime(2026, 1, 4, 10, 0)),
            ("2026-01-02", date(2026, 1, 4)),
            (date(2026, 1, 2), 20260104),
        ],
        ids=[
            "check_in_es_datetime",
            "check_out_es_datetime",
            "check_in_es_cadena",
            "check_out_es_entero",
        ],
    )
    def test_tipo_de_fecha_invalido(self, check_in, check_out):
        with pytest.raises(TypeError):
            nights(check_in, check_out)


class TestNightlyRate:
    """Casos de la tarifa por noche (`nightly_rate`)."""

    @pytest.mark.parametrize(
        ("room", "esperado"),
        [
            ("single", Decimal("50.00")),
            ("double", Decimal("80.00")),
            ("suite", Decimal("150.00")),
        ],
        ids=["single", "double", "suite"],
    )
    def test_tarifa_base_sin_recargo(self, room, esperado):
        # 2026-01-05 es lunes: no lleva recargo.
        assert nightly_rate(date(2026, 1, 5), room) == esperado

    @pytest.mark.parametrize(
        "day",
        [date(2026, 1, 5), date(2026, 1, 6), date(2026, 1, 7), date(2026, 1, 8)],
        ids=["lunes", "martes", "miercoles", "jueves"],
    )
    def test_los_dias_de_semana_no_llevan_recargo(self, day):
        assert nightly_rate(day, "double") == Decimal("80.00")

    def test_recargo_de_la_noche_de_viernes(self):
        # 2026-01-02 es viernes: 80.00 con un recargo del 25 % son 100.00.
        assert nightly_rate(date(2026, 1, 2), "double") == Decimal("100.00")

    def test_recargo_de_la_noche_de_sabado(self):
        # 2026-01-03 es sábado: 80.00 con un recargo del 25 % son 100.00.
        assert nightly_rate(date(2026, 1, 3), "double") == Decimal("100.00")

    def test_la_noche_de_domingo_no_lleva_recargo(self):
        # 2026-01-04 es domingo.
        assert nightly_rate(date(2026, 1, 4), "double") == Decimal("80.00")

    def test_recargo_sobre_la_tarifa_de_suite(self):
        # 150.00 con un recargo del 25 % son 187.50.
        assert nightly_rate(date(2026, 1, 2), "suite") == Decimal("187.50")

    def test_recargo_sobre_la_tarifa_individual(self):
        # 50.00 con un recargo del 25 % son 62.50.
        assert nightly_rate(date(2026, 1, 2), "single") == Decimal("62.50")

    def test_el_resultado_es_un_decimal_con_dos_decimales(self):
        resultado = nightly_rate(date(2026, 1, 2), "double")

        assert isinstance(resultado, Decimal)
        assert resultado.as_tuple().exponent == -2


class TestNightlyRateErrores:
    """Casos de habitación desconocida y de fecha inválida."""

    @pytest.mark.parametrize(
        "room",
        ["deluxe", "Double", "SINGLE", ""],
        ids=["deluxe", "Double", "SINGLE", "vacio"],
    )
    def test_habitacion_desconocida(self, room):
        with pytest.raises(ValueError):
            nightly_rate(date(2026, 1, 5), room)

    @pytest.mark.parametrize(
        "room",
        [None, 42, ["double"]],
        ids=["none", "entero", "lista"],
    )
    def test_habitacion_de_tipo_invalido(self, room):
        with pytest.raises(ValueError):
            nightly_rate(date(2026, 1, 5), room)

    @pytest.mark.parametrize(
        "day",
        [datetime(2026, 1, 2, 15, 30), "2026-01-02", 20260102],
        ids=["day_es_datetime", "day_es_cadena", "day_es_entero"],
    )
    def test_tipo_de_fecha_invalido(self, day):
        with pytest.raises(TypeError):
            nightly_rate(day, "double")


class TestStayTotal:
    """Casos del total de la estadía (`stay_total`)."""

    def test_ejemplo_del_enunciado(self):
        # Del 2026-01-02 (viernes) al 2026-01-04: dos noches de 100.00 más
        # 2.50 de tasa turística por huésped y noche.
        total = stay_total(date(2026, 1, 2), date(2026, 1, 4), "double", 2)

        assert total == Decimal("210.00")

    def test_la_noche_del_dia_de_check_out_no_se_cobra(self):
        # Un huésped: 200.00 de habitación por dos noches más 5.00 de tasa.
        total = stay_total(date(2026, 1, 2), date(2026, 1, 4), "double", 1)

        assert total == Decimal("205.00")

    def test_la_tasa_turistica_escala_con_huespedes_y_noches(self):
        # Una noche en individual: 50.00 de habitación más 2.50 de tasa.
        total = stay_total(date(2026, 1, 5), date(2026, 1, 6), "single", 1)

        assert total == Decimal("52.50")

    def test_el_resultado_es_un_decimal_con_dos_decimales(self):
        total = stay_total(date(2026, 1, 2), date(2026, 1, 4), "double", 2)

        assert isinstance(total, Decimal)
        assert total.as_tuple().exponent == -2

    def test_huespedes_iguales_a_la_capacidad_de_la_suite(self):
        # Cuatro huéspedes en suite: 375.00 de habitación más 20.00 de tasa.
        total = stay_total(date(2026, 1, 2), date(2026, 1, 4), "suite", 4)

        assert total == Decimal("395.00")


class TestStayTotalDescuento:
    """Casos del descuento por estadía larga."""

    def test_estadia_de_seis_noches_sin_descuento(self):
        # 520.00 de habitación sin descuento más 30.00 de tasa turística.
        total = stay_total(date(2026, 1, 5), date(2026, 1, 11), "double", 2)

        assert total == Decimal("550.00")

    def test_estadia_de_siete_noches_con_descuento(self):
        # 600.00 de habitación con el 10 % de descuento son 540.00, más
        # 35.00 de tasa turística sin descuento.
        total = stay_total(date(2026, 1, 5), date(2026, 1, 12), "double", 2)

        assert total == Decimal("575.00")

    def test_la_tasa_turistica_no_recibe_el_descuento(self):
        # 375.00 de habitación con el 10 % de descuento son 337.50, más
        # 17.50 de tasa turística sin descuento.
        total = stay_total(date(2026, 1, 5), date(2026, 1, 12), "single", 1)

        assert total == Decimal("355.00")


class TestStayTotalErroresDeFechas:
    """Casos de fechas no posteriores o de una estadía demasiado larga."""

    def test_check_out_anterior_al_check_in(self):
        with pytest.raises(ValueError):
            stay_total(date(2026, 1, 10), date(2026, 1, 5), "double", 2)

    def test_check_out_igual_al_check_in(self):
        with pytest.raises(ValueError):
            stay_total(date(2026, 1, 10), date(2026, 1, 10), "double", 2)

    def test_estadia_de_31_noches(self):
        with pytest.raises(ValueError):
            stay_total(date(2026, 1, 1), date(2026, 2, 1), "double", 2)

    @pytest.mark.parametrize(
        ("check_in", "check_out"),
        [
            (datetime(2026, 1, 2, 15, 30), date(2026, 1, 4)),
            (date(2026, 1, 2), datetime(2026, 1, 4, 10, 0)),
            ("2026-01-02", date(2026, 1, 4)),
            (date(2026, 1, 2), 20260104),
        ],
        ids=[
            "check_in_es_datetime",
            "check_out_es_datetime",
            "check_in_es_cadena",
            "check_out_es_entero",
        ],
    )
    def test_tipo_de_fecha_invalido(self, check_in, check_out):
        with pytest.raises(TypeError):
            stay_total(check_in, check_out, "double", 2)


class TestStayTotalErroresDeHabitacion:
    """Casos de habitación desconocida en el total de la estadía."""

    @pytest.mark.parametrize(
        "room",
        ["presidential", "deluxe", "Double", ""],
        ids=["presidential", "deluxe", "Double", "vacio"],
    )
    def test_habitacion_desconocida(self, room):
        with pytest.raises(ValueError):
            stay_total(date(2026, 1, 2), date(2026, 1, 4), room, 2)


class TestStayTotalErroresDeHuespedes:
    """Casos de número de huéspedes inválido."""

    @pytest.mark.parametrize(
        "guests",
        [True, False, 2.0, 2.5, "2", None],
        ids=[
            "booleano_verdadero",
            "booleano_falso",
            "flotante_entero",
            "flotante_decimal",
            "cadena",
            "none",
        ],
    )
    def test_tipo_de_huespedes_invalido(self, guests):
        with pytest.raises(TypeError):
            stay_total(date(2026, 1, 2), date(2026, 1, 4), "double", guests)

    @pytest.mark.parametrize("guests", [0, -1], ids=["cero", "negativo"])
    def test_huespedes_por_debajo_del_minimo(self, guests):
        with pytest.raises(ValueError):
            stay_total(date(2026, 1, 2), date(2026, 1, 4), "double", guests)

    @pytest.mark.parametrize(
        ("room", "guests"),
        [("single", 2), ("double", 3), ("suite", 5)],
        ids=["single", "double", "suite"],
    )
    def test_huespedes_por_encima_de_la_capacidad(self, room, guests):
        with pytest.raises(ValueError):
            stay_total(date(2026, 1, 2), date(2026, 1, 4), room, guests)
