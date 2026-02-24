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
    path('zonas/', views.ZonaListView.as_view(), name='zona-list'),
    path('zonas/<int:pk>/', views.ZonaDetailView.as_view(), name='zona-detail'),
    path('zonas/create/', views.ZonaCreateView.as_view(), name='zona-create'),
    path('zonas/<int:pk>/update/', views.ZonaUpdateView.as_view(), name='zona-update'),
    path('zonas/<int:pk>/delete/', views.ZonaDeleteView.as_view(), name='zona-delete'),
    path('zonas/<int:pk>/guardar-sesion/', views.guardar_zona_sesion_view, name='guardar-zona-sesion'),
    path('enemigos/', views.EnemigoListView.as_view(), name='enemigo-list'),
    path('enemigos/<int:pk>/', views.EnemigoDetailView.as_view(), name='enemigo-detail'),
    path('enemigos/create/', views.EnemigoCreateView.as_view(), name='enemigo-create'),
    path('enemigos/<int:pk>/update/', views.EnemigoUpdateView.as_view(), name='enemigo-update'),
    path('enemigos/<int:pk>/delete/', views.EnemigoDeleteView.as_view(), name='enemigo-delete'),
    path('estadisticas/', views.estadisticas_view, name='estadisticas'),
    path('cambiar-tema/', views.cambiar_tema_view, name='cambiar-tema'),
]
