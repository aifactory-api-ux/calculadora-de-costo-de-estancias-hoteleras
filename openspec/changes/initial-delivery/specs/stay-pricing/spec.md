# Spec Delta

## Purpose

Define las reglas de precio de una estadía: tarifa base por tipo de habitación, recargo de fin de semana, tasa turística por huésped y noche, descuento por estadía larga, redondeo monetario y validación de habitación y huéspedes.

## ADDED Requirements

### Requirement: Tarifa base por tipo de habitación

La función `nightly_rate(day, room)` MUST devolver, como `Decimal`, la tarifa base de la noche que comienza en `day` para el tipo de habitación indicado: `single` 50.00, `double` 80.00 y `suite` 150.00.

#### Scenario: Habitación individual en un día sin recargo

- **WHEN** se solicita `nightly_rate(date(2026, 1, 5), "single")`
- **THEN** devuelve el `Decimal` `50.00`

#### Scenario: Habitación doble en un día sin recargo

- **WHEN** se solicita `nightly_rate(date(2026, 1, 5), "double")`
- **THEN** devuelve el `Decimal` `80.00`

#### Scenario: Habitación suite en un día sin recargo

- **WHEN** se solicita `nightly_rate(date(2026, 1, 5), "suite")`
- **THEN** devuelve el `Decimal` `150.00`

### Requirement: Recargo del 25 % en las noches de viernes y sábado

La función `nightly_rate` MUST aplicar un recargo del 25 % sobre la tarifa base en la noche que comienza en viernes y en la noche que comienza en sábado, y MUST NOT aplicarlo en ningún otro día de la semana.

#### Scenario: Noche de viernes

- **WHEN** se solicita `nightly_rate(date(2026, 1, 2), "double")` y el 2 de enero de 2026 es viernes
- **THEN** devuelve el `Decimal` `100.00` (80.00 con recargo del 25 %)

#### Scenario: Noche de sábado

- **WHEN** se solicita `nightly_rate(date(2026, 1, 3), "double")` y el 3 de enero de 2026 es sábado
- **THEN** devuelve el `Decimal` `100.00` (80.00 con recargo del 25 %)

#### Scenario: Noche de domingo sin recargo

- **WHEN** se solicita `nightly_rate(date(2026, 1, 4), "double")` y el 4 de enero de 2026 es domingo
- **THEN** devuelve el `Decimal` `80.00` sin recargo

#### Scenario: Recargo sobre la tarifa de suite

- **WHEN** se solicita `nightly_rate(date(2026, 1, 2), "suite")`
- **THEN** devuelve el `Decimal` `187.50` (150.00 con recargo del 25 %)

### Requirement: Redondeo monetario a 2 decimales con ROUND_HALF_UP

Todos los importes monetarios devueltos por la librería MUST ser valores `Decimal` con exactamente 2 decimales, redondeados con `ROUND_HALF_UP`.

#### Scenario: Importe con más de 2 decimales

- **WHEN** el importe calculado requiere más de 2 decimales
- **THEN** el valor devuelto está cuantizado a 2 decimales usando `ROUND_HALF_UP`

#### Scenario: Aritmética decimal exacta

- **WHEN** se calcula el total de una estadía
- **THEN** el cálculo se realiza con `decimal.Decimal` y no con números de coma flotante, por lo que el importe devuelto coincide exactamente con el valor decimal esperado

### Requirement: Habitación desconocida

La función `nightly_rate` MUST lanzar `ValueError` cuando el tipo de habitación no sea uno de `single`, `double` o `suite`.

#### Scenario: Nombre de habitación no soportado

- **WHEN** se solicita `nightly_rate(date(2026, 1, 5), "deluxe")`
- **THEN** se lanza `ValueError`

#### Scenario: Nombre de habitación con otro formato de mayúsculas

- **WHEN** se solicita `nightly_rate(date(2026, 1, 5), "Double")`
- **THEN** se lanza `ValueError`

### Requirement: Validación del tipo de la fecha de la noche

La función `nightly_rate` MUST lanzar `TypeError` cuando `day` no sea una instancia de `datetime.date`, y también cuando sea una instancia de `datetime.datetime`.

#### Scenario: La fecha es un `datetime.datetime`

- **WHEN** se solicita `nightly_rate(datetime(2026, 1, 2, 15, 30), "double")`
- **THEN** se lanza `TypeError`

#### Scenario: La fecha es una cadena de texto

- **WHEN** se solicita `nightly_rate("2026-01-02", "double")`
- **THEN** se lanza `TypeError`

### Requirement: Total de la estadía como suma de tarifas y tasa turística

La función `stay_total(check_in, check_out, room, guests)` MUST devolver la suma de la tarifa de cada noche de la estadía, desde la noche que comienza en `check_in` hasta la noche que comienza el día anterior a `check_out`, más una tasa turística de `2.50` por huésped y por noche.

#### Scenario: Ejemplo del enunciado

- **WHEN** se solicita `stay_total(date(2026, 1, 2), date(2026, 1, 4), "double", 2)`
- **THEN** devuelve el `Decimal` `210.00` (100.00 + 100.00 de habitación y 10.00 de tasa turística)

#### Scenario: La noche del día de check-out no se cobra

- **WHEN** se solicita `stay_total(date(2026, 1, 2), date(2026, 1, 4), "double", 1)`
- **THEN** devuelve el `Decimal` `205.00` (200.00 de habitación por dos noches y 5.00 de tasa turística por un huésped y dos noches)

#### Scenario: La tasa turística escala con huéspedes y noches

- **WHEN** se solicita `stay_total(date(2026, 1, 5), date(2026, 1, 6), "single", 1)`
- **THEN** devuelve el `Decimal` `52.50` (50.00 de habitación y 2.50 de tasa turística)

### Requirement: Descuento del 10 % a partir de 7 noches

La función `stay_total` MUST aplicar un descuento del 10 % cuando la estadía sea de 7 noches o más, y MUST aplicarlo únicamente sobre el subtotal de habitación, sin afectar a la tasa turística.

#### Scenario: Estadía de 6 noches sin descuento

- **WHEN** se solicita `stay_total(date(2026, 1, 5), date(2026, 1, 11), "double", 2)`
- **THEN** devuelve el `Decimal` `550.00` (520.00 de habitación sin descuento y 30.00 de tasa turística)

#### Scenario: Estadía de 7 noches con descuento sobre el subtotal de habitación

- **WHEN** se solicita `stay_total(date(2026, 1, 5), date(2026, 1, 12), "double", 2)`
- **THEN** devuelve el `Decimal` `575.00` (600.00 de habitación con el 10 % de descuento, es decir 540.00, y 35.00 de tasa turística sin descuento)

#### Scenario: La tasa turística no recibe el descuento

- **WHEN** se solicita `stay_total(date(2026, 1, 5), date(2026, 1, 12), "single", 1)`
- **THEN** devuelve el `Decimal` `355.00` (375.00 de habitación con el 10 % de descuento, es decir 337.50, y 17.50 de tasa turística sin descuento)

### Requirement: Validación de las fechas y de la habitación en el total

La función `stay_total` MUST lanzar `TypeError` cuando `check_in` o `check_out` no sean `datetime.date` o sean `datetime.datetime`, MUST lanzar `ValueError` cuando `check_out` no sea posterior a `check_in` o la estadía supere las 30 noches, y MUST lanzar `ValueError` cuando el tipo de habitación no sea `single`, `double` o `suite`.

#### Scenario: Check-out anterior al check-in

- **WHEN** se solicita `stay_total(date(2026, 1, 10), date(2026, 1, 5), "double", 2)`
- **THEN** se lanza `ValueError`

#### Scenario: Estadía de 31 noches

- **WHEN** se solicita `stay_total(date(2026, 1, 1), date(2026, 2, 1), "double", 2)`
- **THEN** se lanza `ValueError`

#### Scenario: Check-in que no es una fecha

- **WHEN** se solicita `stay_total("2026-01-02", date(2026, 1, 4), "double", 2)`
- **THEN** se lanza `TypeError`

#### Scenario: Habitación desconocida

- **WHEN** se solicita `stay_total(date(2026, 1, 2), date(2026, 1, 4), "presidential", 2)`
- **THEN** se lanza `ValueError`

### Requirement: Validación del número de huéspedes

La función `stay_total` MUST lanzar `TypeError` cuando `guests` no sea una instancia de `int` o sea un `bool`, y MUST lanzar `ValueError` cuando `guests` sea menor que 1 o mayor que la capacidad de la habitación (1 para `single`, 2 para `double` y 4 para `suite`).

#### Scenario: Número de huéspedes boolean

- **WHEN** se solicita `stay_total(date(2026, 1, 2), date(2026, 1, 4), "double", True)`
- **THEN** se lanza `TypeError`

#### Scenario: Número de huéspedes de tipo flotante

- **WHEN** se solicita `stay_total(date(2026, 1, 2), date(2026, 1, 4), "double", 2.0)`
- **THEN** se lanza `TypeError`

#### Scenario: Cero huéspedes

- **WHEN** se solicita `stay_total(date(2026, 1, 2), date(2026, 1, 4), "double", 0)`
- **THEN** se lanza `ValueError`

#### Scenario: Más huéspedes que la capacidad de la habitación individual

- **WHEN** se solicita `stay_total(date(2026, 1, 2), date(2026, 1, 4), "single", 2)`
- **THEN** se lanza `ValueError`

#### Scenario: Más huéspedes que la capacidad de la habitación doble

- **WHEN** se solicita `stay_total(date(2026, 1, 2), date(2026, 1, 4), "double", 3)`
- **THEN** se lanza `ValueError`

#### Scenario: Más huéspedes que la capacidad de la suite

- **WHEN** se solicita `stay_total(date(2026, 1, 2), date(2026, 1, 4), "suite", 5)`
- **THEN** se lanza `ValueError`

#### Scenario: Número de huéspedes igual a la capacidad

- **WHEN** se solicita `stay_total(date(2026, 1, 2), date(2026, 1, 4), "suite", 4)`
- **THEN** devuelve el `Decimal` `395.00` (375.00 de habitación y 20.00 de tasa turística por cuatro huéspedes y dos noches)
