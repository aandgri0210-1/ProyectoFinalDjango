from django.urls import path

from . import views

app_name = 'juego'

urlpatterns = [
    path("inicio-sesion/", views.login_view, name="inicio-sesion"),
    path("cerrar-sesion/", views.logout_view, name="cerrar-sesion"),
    path("registro/", views.register_view, name="registro"),
    path("personajes/", views.ListaPersonajesView.as_view(), name="personaje-lista"),
    path("personajes/crear/", views.CrearPersonajeView.as_view(), name="personaje-crear"),
    path("personajes/<int:pk>/", views.DetallePersonajeView.as_view(), name="personaje-detalle"),
    path("personajes/<int:pk>/editar/", views.EditarPersonajeView.as_view(), name="personaje-editar"),
    path("personajes/<int:pk>/eliminar/", views.EliminarPersonajeView.as_view(), name="personaje-eliminar"),
    path("personajes/<int:personaje_id>/inventario/", views.ver_inventario, name="inventario-ver"),
    path("personajes/<int:personaje_id>/inventario/agregar/", views.agregar_objeto_inventario, name="inventario-agregar"),
    path("personajes/<int:personaje_id>/inventario/usar/", views.usar_consumible, name="inventario-usar"),
    path("personajes/<int:personaje_id>/tema/", views.fijar_tema, name="tema-fijar"),
]
