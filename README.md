# hotel-booking

Librería Python para calcular el costo de las estadías de un hotel: duración de
la estadía, tarifa por noche con recargo de fin de semana, tasa turística y
descuento por estadía larga.

Es una librería sin servidor, sin base de datos y sin interfaz: solo funciones
puras que el equipo de revenue puede usar como dependencia dentro de sus
scripts.

## Requisitos

- Python 3.9 o superior.
- Ninguna dependencia de ejecución: la librería solo usa `datetime` y `decimal`
  de la librería estándar.

## Instalación

Desde la raíz del repositorio, en un entorno virtual:

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
```

Si el entorno no tiene acceso a red para resolver el backend de compilación,
la instalación puede hacerse sin aislamiento de compilación:

```bash
pip install --no-build-isolation .
```

Para instalar también la dependencia de desarrollo (pytest):

```bash
pip install ".[dev]"
```

### Uso sin instalación

El código de la librería vive en `src/`. Para consumirlo sin instalar la
distribución basta con añadir ese directorio al `PYTHONPATH`:

```bash
PYTHONPATH=src python mi_script.py
```

## Importación

El nombre público del módulo es `booking` (la distribución `hotel-booking` lo
publica como módulo suelto, sin el prefijo `src.`):

```python
from booking import nights, nightly_rate, stay_total
```

## API

### `nights(check_in, check_out) -> int`

Devuelve el número de noches de la estadía: la diferencia en días entre
`check_out` y `check_in`, incluyendo la noche que comienza en `check_in` y
excluyendo la noche que comienza en `check_out`.

| Parámetro | Tipo | Descripción |
| --- | --- | --- |
| `check_in` | `datetime.date` | Fecha de entrada. |
| `check_out` | `datetime.date` | Fecha de salida, posterior a `check_in`. |

La estadía máxima admitida es de 30 noches.

```python
from datetime import date

from booking import nights

noches = nights(date(2026, 1, 2), date(2026, 1, 4))
print(noches)  # 2
```

#### Errores

| Situación | Excepción | Mensaje |
| --- | --- | --- |
| El argumento no es `datetime.date` | `TypeError` | `check_in debe ser datetime.date: str` |
| El argumento es `datetime.datetime` | `TypeError` | `check_in debe ser datetime.date, no datetime.datetime: datetime.datetime(2026, 1, 2, 15, 30)` |
| `check_out` es anterior o igual a `check_in` | `ValueError` | `check_out debe ser posterior a check_in (check_in=2026-01-10, check_out=2026-01-05)` |
| La estadía supera las 30 noches | `ValueError` | `la estadía no puede superar 30 noches (recibidas: 31)` |

`datetime.datetime` se rechaza de forma explícita porque hereda de
`datetime.date`: la hora no aporta información en una fecha de check-in o de
check-out y aceptarla ocultaría el error de quien llama.

### `nightly_rate(day, room) -> Decimal`

Devuelve la tarifa de la noche que **comienza** en `day` para el tipo de
habitación indicado, como `Decimal` con exactamente dos decimales.

#### Tarifa base por tipo de habitación

| Habitación | Tarifa base por noche |
| --- | --- |
| `single` | 50.00 |
| `double` | 80.00 |
| `suite` | 150.00 |

#### Recargo de fin de semana

Las noches que comienzan en **viernes** y en **sábado** llevan un recargo del
**25 %** sobre la tarifa base:

| Noche | Tarifa base (`double`) | Con recargo del 25 % |
| --- | --- | --- |
| Viernes | 80.00 | 100.00 |
| Sábado | 80.00 | 100.00 |
| Domingo a jueves | 80.00 | 80.00 |

El recargo se aplica a la noche que comienza en el día indicado: la noche del
viernes es la del viernes al sábado, y la del sábado es la del sábado al
domingo. Ningún otro día de la semana lo lleva.

#### Redondeo

Todos los importes se calculan con `decimal.Decimal` (nunca con números de
coma flotante) y se redondean a **2 decimales** con `ROUND_HALF_UP`, es
decir, los medios céntimos se redondean hacia arriba.

```python
from datetime import date

from booking import nightly_rate

print(nightly_rate(date(2026, 1, 5), "single"))  # 50.00 (lunes, sin recargo)
print(nightly_rate(date(2026, 1, 5), "double"))  # 80.00 (lunes, sin recargo)
print(nightly_rate(date(2026, 1, 5), "suite"))   # 150.00 (lunes, sin recargo)
print(nightly_rate(date(2026, 1, 2), "double"))  # 100.00 (viernes, con recargo)
print(nightly_rate(date(2026, 1, 3), "double"))  # 100.00 (sábado, con recargo)
print(nightly_rate(date(2026, 1, 4), "double"))  # 80.00 (domingo, sin recargo)
print(nightly_rate(date(2026, 1, 2), "suite"))   # 187.50 (viernes, con recargo)
```

| Parámetro | Tipo | Descripción |
| --- | --- | --- |
| `day` | `datetime.date` | Fecha en la que comienza la noche. |
| `room` | `str` | Tipo de habitación: `single`, `double` o `suite`. |

#### Errores

| Situación | Excepción | Mensaje |
| --- | --- | --- |
| `day` no es `datetime.date` | `TypeError` | `day debe ser datetime.date: str` |
| `day` es `datetime.datetime` | `TypeError` | `day debe ser datetime.date, no datetime.datetime: datetime.datetime(2026, 1, 2, 15, 30)` |
| La habitación no existe | `ValueError` | `habitación desconocida: 'deluxe' (disponibles: double, single, suite)` |

Los nombres de habitación son **exactos y sensibles a mayúsculas**: `"Double"`
no es una habitación válida y produce `ValueError`.

### `stay_total(check_in, check_out, room, guests) -> Decimal`

Devuelve el total de la estadía: la suma de la tarifa de cada noche (desde la
noche que comienza en `check_in` hasta la noche que comienza el día anterior a
`check_out`) más la tasa turística, como `Decimal` con exactamente dos
decimales.

| Parámetro | Tipo | Descripción |
| --- | --- | --- |
| `check_in` | `datetime.date` | Fecha de entrada. |
| `check_out` | `datetime.date` | Fecha de salida, posterior a `check_in`. |
| `room` | `str` | Tipo de habitación: `single`, `double` o `suite`. |
| `guests` | `int` | Número de huéspedes, entre 1 y la capacidad de la habitación. |

#### Capacidad por tipo de habitación

| Habitación | Tarifa base por noche | Huéspedes admitidos |
| --- | --- | --- |
| `single` | 50.00 | 1 |
| `double` | 80.00 | 2 |
| `suite` | 150.00 | 4 |

El número de huéspedes no puede superar la capacidad de la habitación reservada.

#### Tasa turística

La tasa turística es de **2.50 por huésped y por noche**. Se suma después del
subtotal de habitación, de modo que nunca recibe el descuento por estadía
larga.

#### Descuento por estadía larga

Las estadías de **7 noches o más** reciben un **10 % de descuento** sobre el
subtotal de habitación. La tasa turística se suma después, sin descontar.

#### Ejemplo completo

Del 2026-01-02 (viernes) al 2026-01-04, en habitación `double` y con 2
huéspedes:

```python
from datetime import date

from booking import stay_total

total = stay_total(date(2026, 1, 2), date(2026, 1, 4), "double", 2)
print(total)  # 210.00
```

Desglose del importe:

| Concepto | Importe |
| --- | --- |
| Noche del 2026-01-02 (viernes, con recargo del 25 %) | 100.00 |
| Noche del 2026-01-03 (sábado, con recargo del 25 %) | 100.00 |
| Subtotal de habitación | 200.00 |
| Tasa turística (2.50 × 2 huéspedes × 2 noches) | 10.00 |
| **Total** | **210.00** |

La noche que comienza el 2026-01-04 no se cobra: la estadía incluye la noche de
entrada y excluye la noche de salida.

#### Errores

| Situación | Excepción | Mensaje |
| --- | --- | --- |
| `check_in` o `check_out` no es `datetime.date` | `TypeError` | `check_in debe ser datetime.date: str` |
| `check_in` o `check_out` es `datetime.datetime` | `TypeError` | `check_in debe ser datetime.date, no datetime.datetime: datetime.datetime(2026, 1, 2, 15, 30)` |
| `check_out` es anterior o igual a `check_in` | `ValueError` | `check_out debe ser posterior a check_in (check_in=2026-01-10, check_out=2026-01-05)` |
| La estadía supera las 30 noches | `ValueError` | `la estadía no puede superar 30 noches (recibidas: 31)` |
| La habitación no existe | `ValueError` | `habitación desconocida: 'presidential' (disponibles: double, single, suite)` |
| `guests` no es un `int` | `TypeError` | `guests debe ser int, no float: 2.0` |
| `guests` no cabe en la habitación | `ValueError` | `guests debe estar entre 1 y la capacidad de la habitación 'double' (2), recibido: 3` |

`bool` se rechaza de forma explícita porque es subclase de `int`: `True` como
número de huéspedes ocultaría el error de quien llama.

## Pruebas

Desde la raíz del repositorio:

```bash
python -m pytest
```

O sobre el archivo de pruebas concreto:

```bash
python -m pytest tests/test_booking.py
```

## Verificación en contenedor

El repositorio incluye una imagen de pruebas definida en el `Dockerfile` de la
raíz (base `python:3.12-slim`) y orquestada por el `docker-compose.yml` de la
raíz, con un único servicio `booking-tests` que construye la imagen y ejecuta
la misma suite de pruebas. No se publican puertos ni se montan volúmenes: la
librería no ofrece servidor ni interfaz.

```bash
docker compose up --build
```

El comando construye la imagen y propaga el código de salida de pytest, de
modo que falla si alguna prueba falla.

El script `run.sh` hace lo mismo tras comprobar que Docker está disponible:

```bash
./run.sh
```

Si el entorno no tiene Docker instalado, `run.sh` lo indica y ejecuta la suite
en el host:

```bash
python -m pytest -q tests/test_booking.py
```

## Alcance actual

Esta entrega documenta las tres funciones públicas de la librería:

- `nights(check_in, check_out)`: duración de la estadía en noches.
- `nightly_rate(day, room)`: tarifa de la noche que comienza en un día, con
  recargo de fin de semana.
- `stay_total(check_in, check_out, room, guests)`: total de la estadía, con
  descuento por estadía larga y tasa turística.

La entrega containerizada (`Dockerfile`, `docker-compose.yml` y `.dockerignore`
en la raíz) ejecuta esa misma suite de pruebas de forma aislada del entorno del
host, manteniendo la importación pública `from booking import ...`.
