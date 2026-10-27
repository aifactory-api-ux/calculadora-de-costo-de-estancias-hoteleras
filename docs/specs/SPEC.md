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


<!-- specs/container-build/spec.md -->
# Spec Delta

## Purpose

Define la entrega containerizada de la librería de booking: la imagen y la orquestación de Docker Compose que la construyen y ejecutan su suite de pruebas, de modo que el proyecto siempre pueda verificarse de forma reproducible y aislada del entorno del host.

## ADDED Requirements

### Requirement: Imagen de la librería construida con Dockerfile

El repositorio MUST incluir un `Dockerfile` en su raíz que construya una imagen con la librería `booking` de `src/booking.py` y las dependencias de prueba necesarias para ejecutar la suite de pruebas, y MUST usar como base una imagen oficial de Python.

#### Scenario: Construcción de la imagen

- **WHEN** se ejecuta `docker build -f Dockerfile .` en la raíz del repositorio
- **THEN** la imagen se construye correctamente a partir del `Dockerfile` de la raíz e incluye el código de `src/booking.py` y las pruebas de `tests/test_booking.py`

#### Scenario: El contenedor no expone servicios

- **WHEN** se inspecciona la imagen construida
- **THEN** no publica ningún puerto ni define un servicio de red, porque la librería no ofrece servidor ni interfaz

### Requirement: Ejecución de la suite de pruebas en el contenedor

El `Dockerfile` MUST definir como comando por defecto la ejecución de la suite de pruebas con pytest sobre `tests/test_booking.py`, y el código de salida del contenedor MUST ser 0 cuando todas las pruebas pasan.

#### Scenario: Ejecución por defecto del contenedor

- **WHEN** se ejecuta el contenedor construido a partir del `Dockerfile`
- **THEN** se ejecuta pytest sobre `tests/test_booking.py` y el contenedor termina con código de salida 0

#### Scenario: La imagen no necesita dependencias de ejecución de la librería

- **WHEN** se inspecciona la instalación de dependencias de la imagen
- **THEN** solo se instala pytest como dependencia de prueba, porque la librería solo usa `datetime` y `decimal` de la librería estándar

### Requirement: Orquestación local con docker-compose

El repositorio MUST incluir un `docker-compose.yml` en su raíz que defina un servicio construido con el `Dockerfile` de la raíz y que ejecute la suite de pruebas de la librería.

#### Scenario: Ejecución del servicio de Compose

- **WHEN** se ejecuta `docker compose up --build` en la raíz del repositorio
- **THEN** el servicio se construye y ejecuta la suite de pruebas, y el comando termina con código de salida 0

#### Scenario: El servicio no publica puertos

- **WHEN** se inspecciona el `docker-compose.yml` de la raíz
- **THEN** el servicio no define puertos publicados, porque el proyecto es una librería sin servidor


<!-- specs/stay-duration/spec.md -->
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


<!-- specs/stay-pricing/spec.md -->
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


# Design

## Context

- Repositorio vacío (primer commit, sin código existente): no hay consumidores actuales, ni convenciones heredadas que respetar, ni contratos que mantener.
- La librería se consumirá como dependencia en scripts Python propiedad del equipo de revenue del hotel, por lo que la superficie pública debe ser pequeña, estable y fácil de importar (`from booking import ...`).
- Restricción de dependencias: la librería solo puede usar la librería estándar (`datetime`, `decimal`). `pytest` queda como dependencia exclusiva de desarrollo y de la imagen de pruebas.
- El equipo de agentes está compuesto únicamente por el agente Developer, que escribe también las pruebas; no hay agentes QA ni DevSec, así que la ejecución de la suite de pruebas y la verificación del contenedor forman parte del propio trabajo del Developer.
- Ver `proposal.md` para la motivación y `specs/stay-duration/spec.md`, `specs/stay-pricing/spec.md` y `specs/container-build/spec.md` para los requisitos normativos.

## Goals / Non-Goals

**Goals:**

- Una única módulo con tres funciones públicas (`nights`, `nightly_rate`, `stay_total`) que implemente todas las reglas de precio sin estado ni efectos secundarios.
- Importable sin instalar nada (`sys.path` con `src`) y también instalable como distribución para los scripts del equipo de revenue.
- Pruebas automatizadas que cubran el ejemplo del enunciado, el recargo de fin de semana, el descuento de 7 noches, los límites y todas las validaciones.
- Una entrega siempre reproducible en contenedores: `Dockerfile` + `docker-compose.yml` en la raíz, ejecutando la suite de pruebas.

**Non-Goals:**

- Servidor HTTP, API REST, CLI, interfaz de usuario o cualquier capa de red: el proyecto es solo una librería.
- Persistencia: no hay base de datos, ni archivos de estado, ni cache.
- Autenticación, autorización, multi-tenancy, auditoría o métricas.
- Internacionalización de la moneda (los importes no llevan símbolo: son `Decimal` en la moneda del hotel) ni configuración por entorno de tarifas, recargos, descuentos o tasa turística.
- Empaquetado como aplicación distribuible (`pip install .` sí, pero sin binario, entry point ni servicio).

## Decisions

### Archivos que se crean (rutas exactas)

| Ruta | Contenido |
| --- | --- |
| `src/booking.py` | Módulo de la librería: constantes de tarifas/capacidades y las tres funciones públicas. |
| `tests/test_booking.py` | Suite pytest con los casos del enunciado y los casos límite y de validación. |
| `pyproject.toml` | Metadatos de la distribución (`hotel-booking`, módulo `booking` en `src`) y configuración de pytest (`pythonpath = ["src"]`). |
| `README.md` | Documento breve: instalación, uso de las tres funciones y ejemplo de salida. |
| `Dockerfile` | Imagen de pruebas de la librería, construida desde la raíz del repositorio. |
| `docker-compose.yml` | Servicio que construye el `Dockerfile` de la raíz y ejecuta la suite de pruebas. |
| `.dockerignore` | Excluye `.git`, `__pycache__`, `.venv`, artefactos de build y caches de pytest del contexto de build. |

No se crea `src/__init__.py`: la distribución expone un módulo suelto (`booking`), no un paquete, de modo que `from booking import nights` funcione igual en los scripts del equipo de revenue con y sin instalación.

### Módulo funcional en lugar de clases

`src/booking.py` expone funciones puras y constantes de módulo. Cada función recibe todos sus datos por parámetro, no hay estado global mutable y el orden de las llamadas no altera resultados.

- Alternativa descartada: clases `Booking`, `RoomType` o `Stay` con métodos. Aportan superficie pública, estado y complejidad de construcción sin necesidad: el dominio son tres cálculos deterministas.

### Tablas de dominio como constantes inmutables del módulo

Las tarifas base (`single` 50.00, `double` 80.00, `suite` 150.00) y las capacidades (`single` 1, `double` 2, `suite` 4) viven como diccionarios constantes a nivel de módulo (`_BASE_RATES`, `_CAPACITY`), en `Decimal` y `int` respectivamente. La coincidencia de nombres es exacta y sensible a mayúsculas: `"Double"` no es una habitación válida.

- Alternativa descartada: leer tarifas de un YAML/JSON externo. Añade un formato de configuración, un modo de fallo más (archivo ausente o mal formado) y un formato de despliegue que el equipo de revenue tendría que gestionar; además abriría la puerta a la configuración por entorno, que está fuera de alcance.

### Validación de tipos mediante un helper privado compartido

Un helper privado `_require_date(value, nombre)` comprueba `isinstance(value, date)` y descarta `datetime` (que hereda de `date`) lanzando `TypeError`; `nights` lo aplica a `check_in` y `check_out`, y `nightly_rate` a `day`. `stay_total` valida `guests` con `isinstance(guests, int)` excluyendo `bool` (`isinstance(True, int)` es `True` en Python, de ahí el caso especial explícito).

- Alternativa descartada: aceptar `datetime` y normalizarlo a `date`. El enunciado exige `TypeError` para `datetime`; truncar la hora ocultaría el error de quien llama.
- El enunciado solo fija la regla de tipo para las fechas de `nights`; se extiende de forma consistente a `nightly_rate(day, ...)` porque el día determina el día de la semana y un valor no-fecha haría el cálculo incoherente.

### Orden de validación determinista en `stay_total`

1. Tipos de `check_in` y `check_out` → `TypeError`.
2. `check_out` posterior a `check_in` y estadía de 30 noches o menos → `ValueError`.
3. Habitación conocida → `ValueError`.
4. Tipo de `guests` (int y no bool) → `TypeError`.
5. `guests` entre 1 y la capacidad de la habitación → `ValueError`.

Fijar el orden evita que dos entradas inválidas produzcan errores distintos según el camino interno del código. `stay_total` delega la validación de fechas en `nights` y la de habitación en el mismo criterio que `nightly_rate`, de modo que ambos caminos de error coinciden.

### Aritmética decimal exacta y redondeo en un solo punto

Todos los importes se calculan con `decimal.Decimal` (nunca con `float`). Constantes: recargo `Decimal("0.25")` (multiplicador `1.25`), descuento `Decimal("0.10")` (multiplicador `0.90`), tasa turística `Decimal("2.50")`. El redondeo a 2 decimales con `ROUND_HALF_UP` se aplica mediante `quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`:

- `nightly_rate` cuantiza el resultado de aplicar el recargo (o la tarifa base) a 2 decimales.
- `stay_total` cuantiza el subtotal de habitación con descuento y el total final a 2 decimales.

La suma de tarifas ya cuantizadas es exacta; el 10 % de descuento sobre un subtotal formado por múltiplos de 0.25 puede producir tres decimales, por eso el subtotal descontado se cuantiza antes de sumarlo a la tasa turística.

- Alternativa descartada: redondear solo al final. Obliga a arrastrar decimales intermedios y deja la decisión de dónde redondear implícita en cada operación.
- Alternativa descartada: `ROUND_HALF_EVEN`. El enunciado fija `ROUND_HALF_UP`.

### Cálculo del total

1. `n = nights(check_in, check_out)`.
2. `subtotal = sum(nightly_rate(check_in + timedelta(days=i), room) for i in range(n))`.
3. Si `n >= 7`: `subtotal = quantize(subtotal * Decimal("0.90"))`; en caso contrario se mantiene el subtotal.
4. `tax = guests * Decimal("2.50") * n`.
5. `total = quantize(subtotal + tax)`.

La noche del día de `check_out` nunca se cobra porque el recorrido `range(n)` cubre desde `check_in` hasta el día anterior. El descuento se aplica solo al subtotal de habitación; la tasa touristica se suma después, sin descontar.

### Configuración de pytest e importación del módulo

`pyproject.toml` declara `[tool.pytest.ini_options] pythonpath = ["src"]`, de forma que `tests/test_booking.py` importe `from booking import nights, nightly_rate, stay_total` sin instalar nada y sin `conftest.py` adicional. La distribución se declara con `py-modules = ["booking"]` y `package-dir = {"" = "src"}`, de modo que `pip install .` en el entorno del equipo de revenue expone el mismo nombre de módulo.

- Alternativa descartada: `src/__init__.py` y `from src.booking import ...`. Obliga a que los scripts del equipo de revenue importen con el prefijo `src.`, que no es un nombre publicable.

### Imagen de pruebas y orquestación

- `Dockerfile`: base `python:3.12-slim`, copia `pyproject.toml`, `src/` y `tests/`, instala `pytest` y define `CMD ["pytest", "-q", "tests/test_booking.py"]`. No publica puertos: no hay servidor.
- `docker-compose.yml`: un único servicio `booking-tests` con `build: .` y `command: pytest -q tests/test_booking.py`, sin puertos publicados ni volúmenes.
- `docker compose up --build` construye la imagen y ejecuta la suite; compose propaga el código de salida del contenedor, de modo que la verificación es "el comando termina con código 0".
- Alternativa descartada: un `docker-compose.yml` con un servicio de aplicación y otro de pruebas. No hay aplicación que ejecutar.

### Reparto del trabajo en el único agente Developer

El equipo se limita al agente Developer, que implementa el módulo, escribe las pruebas de cada grupo de tareas y ejecuta la suite (en local y en el contenedor) como parte de su propia verificación. No se planifican tareas de QA ni de DevSec, ni pasos de revisión de seguridad automatizada; el control de calidad se apoya en las pruebas automatizadas y en la validación de OpenSpec.

## Migration Plan

- No hay migración: es la primera entrega y no existen consumidores previos.
- Publicación para el equipo de revenue: `pip install .` en un entorno virtual, o simplemente añadir `src/` al `sys.path` de sus scripts. El nombre del módulo importado es `booking`.
- Reversión: eliminar la instalación del paquete (`pip uninstall hotel-booking`) y, si se distribuye como código, retirar el directorio `src/`. No hay estado que limpiar ni datos que migrar.

## Risks / Trade-offs

- [El redondeo solo al final puede producir discrepancias de 0.01 frente a cálculos hechos con `float` a mano] → Todo el cálculo usa `Decimal` y el redondeo `ROUND_HALF_UP` a 2 decimales está especificado en `specs/stay-pricing/spec.md`; las pruebas fijan los importes exactos esperados.
- [La validación de tipo de `day` en `nightly_rate` y el nombre de habitación sensible a mayúsculas no están enunciados de forma explícita] → Se documentan como supuestos explícitos en la especificación y en el README, para que el equipo de revenue no tenga que adivinarlos.
- [La imagen depende de `python:3.12-slim` y de la red de Docker Hub al construir] → Se fija la etiqueta de versión de la imagen base y se documenta `docker compose up --build` como paso de verificación; la suite local con pytest sigue siendo la vía rápida de comprobación.
- [Sin `src/__init__.py`, un `pip install .` mal configurado deja el módulo sin localizar] → `pyproject.toml` declara `py-modules = ["booking"]` con `package-dir = {"" = "src"}` y el README documenta la instalación y el uso de `PYTHONPATH=src`.
- [El contenedor solo ejecuta pruebas, no valida el empaquetado instalado] → El `Dockerfile` copia `src/` y `tests/` y ejecuta pytest con `pythonpath` configurado; además se documenta en el README el uso de `pip install .` para los consumidores.
