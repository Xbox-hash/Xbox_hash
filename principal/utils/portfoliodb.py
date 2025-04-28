from django.conf import settings
from pymongo import MongoClient # type: ignore

def conectar_db():
    #conexion de la base de datos
    cliente = MongoClient(settings.MONGODB_CONFIG['HOST'], settings.MONGODB_CONFIG['PORT'])
    db = cliente[settings.MONGODB_CONFIG['DB_NAME']]
    coleccion = db["proyectos"]
    return coleccion