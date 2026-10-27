"""Marcador de paquete de la raiz del repositorio.

El proyecto se distribuye como un modulo suelto: la distribucion `hotel-booking`
publica el modulo `booking` cuyo codigo reside en el directorio `src`, por lo
que la importacion publica es:

    from booking import nights, nightly_rate, stay_total

Este archivo no contiene logica de negocio: unicamente declara la raiz como
paquete para las herramientas que esperan un marcador de paquete.
"""
