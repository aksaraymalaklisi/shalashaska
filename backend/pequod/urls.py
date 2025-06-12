from django.urls import path
from .views import PathfinderView  # Importe a nova classe

urlpatterns = [
    # A URL pode permanecer a mesma, mas agora aponta para a view do DRF
    path(
        'pathfinder/<str:network_type>/', 
        PathfinderView.as_view(), 
        name='pathfinder_api'
    ),
    # ... outras urls do seu app
]
