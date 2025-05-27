from django.urls import path
from . import views # Importa as views do app atual

# Padrão para namespaces de URL (recomendado)
app_name = 'pequod'

urlpatterns = [
    path('pathfinder/<str:network_type>/', views.pathfinder_view, name='pathfinder'),
]