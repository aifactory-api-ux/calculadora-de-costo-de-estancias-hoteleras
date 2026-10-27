# Imagen de pruebas de la librería hotel-booking.
#
# El proyecto es una librería sin servidor ni interfaz: el contenedor solo
# ejecuta la suite de pruebas de pytest sobre tests/test_booking.py y termina
# con el código de salida de pytest.

FROM python:3.12-slim

# Sin bytecode compilado y con la salida sin búfer, para que el informe de
# pytest llegue íntegro a la consola. PYTHONPATH apunta al código de la
# librería, de modo que `from booking import ...` funcione sin instalarla.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# La distribución no se instala en la imagen: la librería solo usa datetime y
# decimal de la librería estándar, de modo que basta con copiar el código y
# exponer src/ en el PYTHONPATH. pytest es la única dependencia instalada.
COPY pyproject.toml ./
COPY src/ ./src/
COPY tests/ ./tests/

RUN pip install --no-cache-dir pytest

# La imagen no publica puertos ni define servicios de red: no hay nada que
# escuchar. El comando por defecto es la propia suite de pruebas.
CMD ["pytest", "-q", "tests/test_booking.py"]
