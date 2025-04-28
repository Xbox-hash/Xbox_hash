from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
from .utils.portfoliodb import conectar_db
from bson import ObjectId
from django.http import HttpResponse


def inicio(request):
    coleccion = conectar_db()
    trabajos = list(coleccion.find().sort("fecha", -1))
    categorias = coleccion.find({}, {"_id": 0, "categoria": 1})
    categorias_unicas = {doc["categoria"] for doc in categorias if "categoria" in doc}
    categorias_unicas = sorted(categorias_unicas)
    return render(
        request, "index.html", {"trabajos": trabajos, "categoria": categorias_unicas}
    )


def portfolio(request):

    if request.method == "GET":
        titulo = request.GET.get("titulo")
        descripcion = request.GET.get("descripcion")
        categoria = request.GET.get("categoria")
        fecha = request.GET.get("fecha")
        imagenes_string = request.GET.get("imagenes", "")
        imagenes = imagenes_string.split(",") if imagenes_string else []

        posteos = {
            "titulo": titulo,
            "descripcion": descripcion,
            "categoria": categoria,
            "fecha": fecha,
            "imagenes": imagenes,
        }

        posteo_db = conectar_db()
        posteo_db.find(posteos)

    return render(request, "portfolio-details.html", {"posteos": posteos})


def service(request):
    return render(request, "service-details.html")


def starter(request):
    return render(request, "starter-page.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def panel_admin(request):
    if request.method == "POST":
        # Aquí puedes manejar la lógica para guardar los datos del formulario
        titulo = request.POST.get("titulo")
        descripcion = request.POST.get("descripcion")
        categoria = request.POST.get("categoria")
        imagenes = request.FILES.getlist("imagenes")
        fecha = request.POST.get("fecha")

        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        rutas_imagenes = []
        for imagen in imagenes:
            nombre_imagen = fs.save(imagen.name, imagen)
            ruta_completa = os.path.join(settings.MEDIA_URL, nombre_imagen)
            rutas_imagenes.append(ruta_completa)
        trabajo = {
            "titulo": titulo,
            "descripcion": descripcion,
            "categoria": categoria,
            "imagenes": rutas_imagenes,
            "fecha": fecha,
        }
        # establecer la conexion con la base de datos
        # e insertar nuevos trabajos
        trabajos_db = conectar_db()
        trabajos_db.insert_one(trabajo)
        return redirect("inicio")

    return render(request, "panel-administracion.html")


def listar_posteos(request):
    if request.method == "GET":
        titulo = request.GET.get("titulo")
        descripcion = request.GET.get("descripcion")
        categoria = request.GET.get("categoria")
        fecha = request.GET.get("fecha")
        imagenes = request.FILES.getlist("imagenes")

        posteos = {
            "titulo": titulo,
            "descripcion": descripcion,
            "categoria": categoria,
            "fecha": fecha,
            "imagenes": imagenes,
        }

        # para listar los posteos ya existentes
        posteo_db = conectar_db()
        posteos = list(posteo_db.find().sort("fecha", -1))

        for post in posteos:
            post["id"] = str(post["_id"])

        return render(request, "posteos.html", {"posteos": posteos})


# logica para editar posteos
def editar_posteo(request, id):
    db = conectar_db()
    
    if request.method == "POST":
        titulo = request.POST.get("titulo")
        descripcion = request.POST.get("descripcion")
        categoria = request.POST.get("categoria")
        fecha = request.POST.get("fecha")

        db.update_one(
            {"_id": ObjectId(id)},
            {
                "$set": {
                    "titulo": titulo,
                    "descripcion": descripcion,
                    "categoria": categoria,
                    "fecha": fecha,
                }
            },
        )
    posteos = db.find_one({"_id": ObjectId(id)})
    return render(
        request, "editar-posteo.html", {"post": posteos}
    )

def elimimar_posteo(request, id):
    db = conectar_db()

    posteo = db.find_one({"_id": ObjectId(id)})
    print(posteo)

    if posteo:
        imagenes = posteo.get("imagenes", [])
        print(imagenes)
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)
        for imagen in imagenes:
            nombre_imagen = imagen.split(settings.MEDIA_URL)[-1]
            archivo_imagen = os.path.join(settings.MEDIA_ROOT, nombre_imagen)

            if os.path.exists(archivo_imagen):
                os.remove(archivo_imagen)

    db.delete_one({"_id": ObjectId(id)})
    return redirect("listar_posteos")
