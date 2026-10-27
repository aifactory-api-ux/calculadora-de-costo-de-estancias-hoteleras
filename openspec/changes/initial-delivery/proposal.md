# Proposal

## Why

El equipo de revenue del hotel necesita calcular el costo de una estadía (noches, tarifa por noche con recargo de fin de semana, tasa turística y descuento por estadía larga) dentro de sus scripts de Python. Hoy no existe una fuente única de verdad para esas reglas de precio, por lo que cada script termina reimplementando el cálculo por su cuenta.

## What Changes

- Se crea la librería `booking` en `src/booking.py`, usando únicamente la librería estándar de Python (`datetime`, `decimal`), que expone:
  - `nights(check_in, check_out) -> int`: número de noches entre dos `datetime.date`, con validación de orden (ValueError) y de estadía máxima de 30 noches (ValueError), y de tipo (TypeError si el argumento no es `date` o es `datetime`).
  - `nightly_rate(day, room) -> Decimal`: tarifa base por tipo de habitación (`single` 50.00, `double` 80.00, `suite` 150.00) con recargo del 25 % en las noches de viernes y sábado, redondeada a 2 decimales con `ROUND_HALF_UP`; habitación desconocida -> ValueError.
  - `stay_total(check_in, check_out, room, guests) -> Decimal`: subtotal de habitación (suma de `nightly_rate` desde `check_in` hasta el día anterior a `check_out`) con 10 % de descuento cuando la estadía es de 7 noches o más (aplicado solo al subtotal de habitación) más la tasa turística de 2.50 por huésped y por noche, redondeado a 2 decimales con `ROUND_HALF_UP`; `guests` debe ser `int` (un `bool` produce TypeError) entre 1 y la capacidad de la habitación (`single` 1, `double` 2, `suite` 4).
- Se añaden las pruebas automatizadas en `tests/test_booking.py` con pytest: ejemplo del enunciado, recargo de fin de semana, descuento de 7 noches, y límites y validaciones (tipos, orden de fechas, máximo de 30 noches, habitación desconocida, huéspedes).
- Se añade un README breve con la instalación y el uso de la librería.
- Se añade la contenerización obligatoria del proyecto: `Dockerfile` en la raíz y `docker-compose.yml` en la raíz, cuyo contenedor ejecuta la suite de pruebas de la librería (no hay servidor ni interfaz).
- Se documenta el modelo de entrega: el equipo de agentes está compuesto únicamente por el agente Developer, que escribe también las pruebas; no hay agentes QA ni DevSec.

## Capabilities

### New Capabilities

- `stay-duration`: reglas de duración de la estadía (`nights`) y validación de los argumentos de fecha (tipo, orden y máximo de 30 noches).
- `stay-pricing`: reglas de precio de la estadía: tarifa base por tipo de habitación, recargo del 25 % de viernes y sábado, tasa turística de 2.50 por huésped y noche, descuento del 10 % a partir de 7 noches sobre el subtotal de habitación, redondeo monetario `ROUND_HALF_UP` a 2 decimales y validación de tipo de habitación y de huéspedes.
- `container-build`: entrega containerizada de la librería: `Dockerfile` y `docker-compose.yml` en la raíz del repositorio que construyen la imagen y ejecutan la suite de pruebas, verificable con `docker compose up --build` con código de salida 0.

### Modified Capabilities

Ninguna. Es la primera entrega del proyecto y no existen especificaciones previas.

## Impact

- Código nuevo: `src/booking.py`, `tests/test_booking.py`, `pyproject.toml`.
- Documentación nueva: `README.md`.
- Contenedores: `Dockerfile`, `docker-compose.yml`, `.dockerignore` en la raíz del repositorio.
- Dependencias: la librería no declara dependencias de ejecución (solo `datetime` y `decimal` de la librería estándar); `pytest` es dependencia exclusiva de desarrollo y de la imagen de pruebas.
- Consumidores: el equipo de revenue del hotel, que usará `booking` como dependencia dentro de sus scripts Python. No hay servidor, base de datos, API HTTP ni interfaz de usuario.
- Superficie pública nueva: los tres funciones `nights`, `nightly_rate` y `stay_total` del módulo `booking`.
