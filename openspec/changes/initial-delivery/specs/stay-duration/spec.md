# Spec Delta

## Purpose

Define las reglas que determinan la duración en noches de una estadía y la validación de los argumentos de fecha que la aceptan, de modo que todo el cálculo de precio se apoye en una única definición de "noche de estadía".

## ADDED Requirements

### Requirement: Cálculo del número de noches de la estadía

La función `nights(check_in, check_out)` MUST devolver el número entero de noches de la estadía, es decir, la diferencia en días entre `check_out` y `check_in`, incluyendo la noche que comienza en `check_in` y excluyendo la noche que comienza en `check_out`.

#### Scenario: Estadía de dos noches

- **WHEN** se solicita `nights(date(2026, 1, 2), date(2026, 1, 4))`
- **THEN** devuelve el entero `2`

#### Scenario: Estadía de una noche

- **WHEN** se solicita `nights(date(2026, 1, 2), date(2026, 1, 3))`
- **THEN** devuelve el entero `1`

#### Scenario: Estadía de exactamente 30 noches

- **WHEN** se solicita `nights(date(2026, 1, 1), date(2026, 1, 31))`
- **THEN** devuelve el entero `30` sin lanzar excepción

### Requirement: `check_out` debe ser posterior a `check_in`

La función `nights` MUST lanzar `ValueError` cuando `check_out` no sea estrictamente posterior a `check_in`.

#### Scenario: Check-out anterior al check-in

- **WHEN** se solicita `nights(date(2026, 1, 10), date(2026, 1, 5))`
- **THEN** se lanza `ValueError`

#### Scenario: Check-out igual al check-in

- **WHEN** se solicita `nights(date(2026, 1, 10), date(2026, 1, 10))`
- **THEN** se lanza `ValueError`

### Requirement: Límite máximo de 30 noches por estadía

La función `nights` MUST lanzar `ValueError` cuando la estadía supere las 30 noches.

#### Scenario: Estadía de 31 noches

- **WHEN** se solicita `nights(date(2026, 1, 1), date(2026, 2, 1))`
- **THEN** se lanza `ValueError`

### Requirement: Validación del tipo de las fechas

La función `nights` MUST lanzar `TypeError` cuando `check_in` o `check_out` no sean instancias de `datetime.date`, y también cuando cualquiera de los dos sea una instancia de `datetime.datetime`, que es subclase de `date`.

#### Scenario: El check-in es un `datetime.datetime`

- **WHEN** se solicita `nights(datetime(2026, 1, 2, 15, 30), date(2026, 1, 4))`
- **THEN** se lanza `TypeError`

#### Scenario: El check-out es un `datetime.datetime`

- **WHEN** se solicita `nights(date(2026, 1, 2), datetime(2026, 1, 4, 10, 0))`
- **THEN** se lanza `TypeError`

#### Scenario: El check-in es una cadena de texto

- **WHEN** se solicita `nights("2026-01-02", date(2026, 1, 4))`
- **THEN** se lanza `TypeError`

#### Scenario: El check-out es un entero

- **WHEN** se solicita `nights(date(2026, 1, 2), 20260104)`
- **THEN** se lanza `TypeError`
