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
