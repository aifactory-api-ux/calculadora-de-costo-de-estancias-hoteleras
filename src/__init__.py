"""Marcador de paquete del directorio `src`.

La libreria se distribuye como un modulo suelto: la distribucion `hotel-booking`
lo publica con `py-modules = ["booking"]` y `package-dir = {"": "src"}`, de modo
que el nombre publico de importacion es `booking`:

    from booking import nights, nightly_rate, stay_total

Este archivo no contiene logica de negocio: solo actua como marcador de paquete
del directorio `src` y no altera el nombre publico de importacion.
"""
