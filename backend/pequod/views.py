import os
import osmnx as ox
import networkx as nx
import logging
from django.conf import settings
from threading import Lock

# Importações do Django Rest Framework
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Importar services e serializers
from .services.pathfinding_service import find_path
from .services.map_utils import download_graph, get_map_key_and_filepath, get_place_name_from_coords
from .serializers import PathfindingRequestSerializer

logger = logging.getLogger(__name__)

# Grafos continuam sendo carregados na memória, mas um LLM veio na minha casa e me ameaçou de morte se eu não usasse um lock.
# Olha isso, ele tá até autocompletamente o resto da ameaça.
LOADED_GRAPHS = {}
graphs_lock = Lock()

PLACE_PREFIX = getattr(settings, 'OSMNX_PLACE_PREFIX', 'marica')
GRAPH_NETWORK_TYPES = ['drive', 'bike', 'walk', 'all'] # Suportando apenas drive, bike e all por enquanto.

for network_type in GRAPH_NETWORK_TYPES:
    key, filepath = get_map_key_and_filepath(PLACE_PREFIX, network_type)
    if os.path.exists(filepath):
        try:
            logger.info(f"Carregando mapa existente: {filepath}")
            G = ox.load_graphml(filepath)
            LOADED_GRAPHS[network_type] = G
        except Exception as e:
            logger.error(f"Erro ao carregar o mapa {filepath} na inicialização: {e}")

class PathfinderView(APIView):
    """
    API para encontrar o caminho mais curto entre dois pontos.
    Se o mapa para a rede solicitada não estiver carregado, ele será baixado sob demanda.
    """
    def get(self, request, network_type):
        # Validação dos parâmetros de entrada com o serializador
        serializer = PathfindingRequestSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data

        # 1. Obter o grafo do OSM usando osmnx (da memória ou via download)
        G = LOADED_GRAPHS.get(network_type)
        if G is None:
            logger.warning(f"Mapa para '{network_type}' não encontrado. Tentando baixar...")
            if network_type not in GRAPH_NETWORK_TYPES:
                return Response({'error': f'Tipo de rede inválido: {network_type}.'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                place_query = settings.OSMNX_PLACE_QUERY
                place_prefix = settings.OSMNX_PLACE_PREFIX
                
                G = download_graph(place_query, place_prefix, network_type)
                with graphs_lock:
                    LOADED_GRAPHS[network_type] = G
                
                logger.info(f"Mapa para '{network_type}' baixado e carregado com sucesso.")

            except Exception as e:
                logger.error(f"Falha ao tentar baixar o mapa para '{network_type}': {e}")
                return Response({'error': 'Serviço temporariamente indisponível, mapa não pôde ser baixado.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 2. Execução do algoritmo de Dijkstra (pathfinding)
        try:
            path_data = find_path(
                G=G,
                start_lat=validated_data['start_lat'],
                start_lon=validated_data['start_lon'],
                end_lat=validated_data['end_lat'],
                end_lon=validated_data['end_lon'],
                network_type=network_type,
                average_speed_kmh=validated_data.get('average_speed_kmh')
            )
            
            # 3. O que é entregue é um JSON contendo todos os latlongs até o destino (quem lida com isso é o DRF)
            return Response(path_data, status=status.HTTP_200_OK)

        except nx.NetworkXNoPath as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Erro inesperado no pathfinding: {e}")
            return Response({'error': 'Ocorreu um erro interno no servidor.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)