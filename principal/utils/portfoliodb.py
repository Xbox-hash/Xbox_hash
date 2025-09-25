from pymongo import MongoClient
import os

def conectar_db():
    MONGO_URI = f"mongodb+srv://{os.environ.get('MONGO_USER')}:{os.environ.get('MONGO_PASS')}@{os.environ.get('MONGO_CLUSTER')}/{os.environ.get('MONGO_DB')}?retryWrites=true&w=majority"
    cliente = MongoClient(MONGO_URI)
    db = cliente.get_database(os.environ.get('MONGO_DB'))
    coleccion = db["proyectos"]
    return coleccion