from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
from .utils.portfoliodb import conectar_db
from bson import ObjectId
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib import messages
import cloudinary.uploader
from django.template.loader import render_to_string
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)

def inicio(request):
    coleccion = conectar_db()
    trabajos = list(coleccion.find().sort("fecha", -1))
    categorias = coleccion.find({}, {"_id": 0, "categoria": 1})
    categorias_unicas = {doc["categoria"] for doc in categorias if "categoria" in doc}
    categorias_unicas = sorted(categorias_unicas)
    return render(
        request, "index.html", {"trabajos": trabajos, "categoria": categorias_unicas,"configuracion": configuracion,}
    )


def portfolio(request):

    if request.method == "GET":
        titulo = request.GET.get("titulo")
        descripcion = request.GET.get("descripcion")
        github_url = request.GET.get("github_url")
        categoria = request.GET.get("categoria")
        fecha = request.GET.get("fecha")
        imagenes_string = request.GET.get("imagenes", "")
        imagenes = imagenes_string.split(",") if imagenes_string else []

        posteos = {
            "titulo": titulo,
            "descripcion": descripcion,
            "github_url": github_url,
            "categoria": categoria,
            "fecha": fecha,
            "imagenes": imagenes  
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
        titulo = request.POST.get("titulo")
        descripcion = request.POST.get("descripcion")
        github_url = request.POST.get("github_url")
        categoria = request.POST.get("categoria")
        imagenes = request.FILES.getlist("imagenes")
        fecha = request.POST.get("fecha")

        rutas_imagenes = []

        for imagen in imagenes:
            # Subir a cloudinary
            resultado = cloudinary.uploader.upload(imagen)
            url_imagen = resultado.get('secure_url')  # URL segura en cloudinary
            rutas_imagenes.append(url_imagen)

        trabajo = {
            "titulo": titulo,
            "descripcion": descripcion,
            "github_url": github_url,
            "categoria": categoria,
            "imagenes": rutas_imagenes,
            "fecha": fecha,
        }

        trabajos_db = conectar_db()
        trabajos_db.insert_one(trabajo)
        return redirect("panel-administracion")

    return render(request, "panel-administracion.html")

@login_required
def listar_posteos(request):
    if request.method == "GET":
        titulo = request.GET.get("titulo")
        descripcion = request.GET.get("descripcion")
        github_url = request.GET.get("github_url")
        categoria = request.GET.get("categoria")
        fecha = request.GET.get("fecha")
        imagenes = request.FILES.getlist("imagenes")


        posteos = {
            "titulo": titulo,
            "descripcion": descripcion,
            "github_url": github_url,
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
@login_required
def editar_posteo(request, id):
    db = conectar_db()
    posteos = db.find_one({"_id": ObjectId(id)})

    if request.method == "POST":
        titulo = request.POST.get("titulo")
        descripcion = request.POST.get("descripcion")
        github_url = request.POST.get("github_url")
        categoria = request.POST.get("categoria")
        fecha = request.POST.get("fecha")
        
        nuevas_imagenes = request.FILES.getlist("imagenes")

        if nuevas_imagenes:
            rutas_imagenes = posteos.get("imagenes", [])
            for imagen in nuevas_imagenes:
                resultado = cloudinary.uploader.upload(imagen)
                url_imagen = resultado.get('secure_url')
                rutas_imagenes.append(url_imagen)
        else:
            rutas_imagenes = posteos.get("imagenes", [])

        db.update_one(
            {"_id": ObjectId(id)},
            {
                "$set": {
                    "titulo": titulo,
                    "descripcion": descripcion,
                    "github_url": github_url,
                    "categoria": categoria,
                    "fecha": fecha,
                    "imagenes": rutas_imagenes,
                }
            },
        )

        return redirect("listar_posteos")

    return render(
        request, "editar-posteo.html", {"post": posteos, "imagenes": posteos.get("imagenes", [])}
    )

def eliminar_posteo(request, id):
    db = conectar_db()
    db.delete_one({"_id": ObjectId(id)})
    return redirect("listar_posteos")

@login_required
def configuracion(request):
    if request.method == "POST":
        foto_perfil = request.FILES.get("foto_perfil")
        fondo = request.FILES.get("fondo")

        data_update = {}

        # Subir foto de perfil
        if foto_perfil:
            resultado = cloudinary.uploader.upload(foto_perfil)
            data_update["foto_perfil"] = resultado.get("secure_url")

        # Subir fondo
        if fondo:
            resultado = cloudinary.uploader.upload(fondo)
            data_update["fondo"] = resultado.get("secure_url")

        if data_update:
            db = conectar_db()
            # Guardamos en una colección "configuracion"
            # Si existe, actualizamos el único documento
            db_config = db.configuracion
            existente = db_config.find_one({})
            if existente:
                db_config.update_one({"_id": existente["_id"]}, {"$set": data_update})
            else:
                db_config.insert_one(data_update)

        return redirect("configuracion")

    # GET → mostrar lo que ya está guardado
    db = conectar_db()
    configuracion = db.configuracion.find_one({}) or {}
    return render(request, "configuracion.html", {"configuracion": configuracion})
