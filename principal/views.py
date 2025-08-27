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
        # Aquí puedes manejar la lógica para guardar los datos del formulario
        titulo = request.POST.get("titulo")
        descripcion = request.POST.get("descripcion")
        github_url = request.POST.get("github_url")
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
            "github_url": github_url,
            "categoria": categoria,
            "imagenes": rutas_imagenes,
            "fecha": fecha,
        }
        # establecer la conexion con la base de datos
        # e insertar nuevos trabajos
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
    posteos = db.find

    if request.method == "POST":
        titulo = request.POST.get("titulo")
        descripcion = request.POST.get("descripcion")
        github_url = request.POST.get("github_url")
        categoria = request.POST.get("categoria")
        fecha = request.POST.get("fecha")
        
        nuevas_imagenes = request.FILES.getlist("imagenes")
        fs = FileSystemStorage(location=settings.MEDIA_ROOT)

        if nuevas_imagenes:
            rutas_imagenes = posteos.get("imagenes", [])
            for imagen in nuevas_imagenes:
                nombre_imagen = fs.save(imagen.name, imagen)
                ruta_completa = os.path.join(settings.MEDIA_URL, nombre_imagen)
                rutas_imagenes.append(ruta_completa)
        else:
            rutas_imagenes = posteos.get("imagenes", [])




        db.update_one(
            {"_id": ObjectId(id)},
            {
                "$set": {
                    "titulo": titulo,
                    "descripcion": descripcion,
                    "github_url":github_url,
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

def contacto(request):
    if request.method == "POST":
        nombre = request.POST["nombre"]
        email = request.POST["email"]
        asunto = request.POST["asunto"]
        mensaje = request.POST["mensaje"]

        template_email = render_to_string('email_template.html', {
            "nombre": nombre,
            "email": email,
            "mensaje": mensaje
        })

        email = EmailMessage(
            asunto,
            template_email,
            settings.EMAIL_HOST_USER,
            ['t9834286@gmail.com']
        )
        email.fail_silently = False
        try:
            email.send()
        except Exception as e:
            print(f"Error al enviar correo: {str(e)}")
        
            messages.error(request, f"Hubo un error al enviar el mensaje: {str(e)}")
        
       
        return HttpResponse('OK')
    return HttpResponse("error", status=404)
    