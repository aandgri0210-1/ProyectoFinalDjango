from django.urls import path
from .views import ZonaListView,ZonaDetailView,ZonaCreateView,ZonaUpdateView, ZonaDeleteView


urlpatterns = [
   path('zonas/', ZonaListView.as_view(), name='zona-list'),
   path('zonas/<int:pk>/', ZonaDetailView.as_view(), name='zona-detail'),
   path('zonas/create/', ZonaCreateView.as_view(), name='zona-create'),
   path('zonas/<int:pk>/update/', ZonaUpdateView.as_view(), name='zona-update'),
   path('zonas/<int:pk>/delete/', ZonaDeleteView.as_view(), name='zona-delete'),
]