#!/usr/bin/env bash
#
# Verificación containerizada de la librería hotel-booking.
#
# Construye la imagen definida en el `Dockerfile` de la raíz y ejecuta la suite
# de pruebas dentro del contenedor. No hay servicios que publicar ni URL que
# abrir: la librería no ofrece servidor, de modo que el script termina con el
# código de salida de la propia suite de pruebas.

set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$RAIZ"

# La librería no usa variables de entorno; si en el futuro existiera un
# `.env.example`, se copiaría a `.env` en la primera ejecución.
if [ -f .env.example ] && [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ .env creado a partir de .env.example"
fi

# Comprobación de Docker antes de construir la imagen.
if ! command -v docker >/dev/null 2>&1; then
    echo "✗ Docker no está instalado: no se puede construir la imagen."
    echo "  Verificación equivalente con la suite en el host:"
    echo "    python -m pytest -q tests/test_booking.py"
    exec python -m pytest -q tests/test_booking.py
fi

echo "→ Construcción de la imagen y ejecución de la suite de pruebas"
echo "  (la librería no publica puertos: no hay URL que abrir)"

# `--exit-code-from` propaga el código de salida de pytest como resultado del
# script, de modo que el proceso falla si alguna prueba falla.
docker compose up --build --abort-on-container-exit --exit-code-from booking-tests
