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
