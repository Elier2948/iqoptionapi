from usuario import api
import time
import sys

while True:
    if not api.check_connect():
        print("error de conexion")
        estado, mensaje = api.connect()
        if estado is None:
            print("error inesperado")
        elif mensaje and "invalid_cedencials" in mensaje:
            print("email o password incorrecto")
            sys.exit()
    else:
        print("conectado a IQoption")
        api.change_balance("PRATICE")# PRATICE O REAL
        break
    time.sleep(1)