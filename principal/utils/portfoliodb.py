from pymongo import MongoClient
import os

def conectar_db():
    MONGO_URI = os.environ.get(
        "MONGO_URI",
        "mongodb+srv://NelsonParr:2004@cluster0.i7uc0xi.mongodb.net/portfolio_db?retryWrites=true&w=majority"
    )
    cliente = MongoClient(MONGO_URI)
    db = cliente.get_database("portfolio_db")
    coleccion = db["proyectos"]
    return coleccion
