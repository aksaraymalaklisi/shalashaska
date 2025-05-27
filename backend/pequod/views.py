import os
import osmnx as ox
import networkx as nx
from django.conf import settings
from django.http import JsonResponse

from .services.pathfinding_service import find_shortest_path

# Carregar os grafos na inicialização do módulo
# Isso carrega os grafos uma vez quando o servidor inicia.
GRAPH_FILENAMES = {
    'drive': 'marica_drive.graphml',
    'bike': 'marica_bike.graphml',
    'walk': 'marica_walk.graphml',
}

LOADED_GRAPHS = {}

for network_type, filename in GRAPH_FILENAMES.items():
    GRAPH_FILEPATH = os.path.join(settings.BASE_DIR, 'map_data', filename)
    try:
        if os.path.exists(GRAPH_FILEPATH):
            print(f"Attempting to load graph for '{network_type}' from: {GRAPH_FILEPATH}")
            G = ox.load_graphml(GRAPH_FILEPATH)
            # Garantir que os atributos de peso sejam do tipo correto (ex: float)
            for _u, _v, data in G.edges(data=True):
                if 'length' in data:
                    data['length'] = float(data['length'])
                # Converta outros atributos de peso se você os tiver (ex: 'travel_time')
            LOADED_GRAPHS[network_type] = G
            print(f"Graph '{filename}' loaded successfully for '{network_type}' with {len(G.nodes())} nodes and {len(G.edges())} edges.")
        else:
            print(f"Graph file not found at {GRAPH_FILEPATH} for network type '{network_type}'. Run 'manage.py fetch_map_data' first.")
            # Note that this function does not exist yet.
    except Exception as e:
        print(f"Error loading graph for '{network_type}' during app initialization: {e}")

def pathfinder_view(request, network_type):
    # Verifica se o grafo para o tipo de rede solicitado foi carregado
    G = LOADED_GRAPHS.get(network_type)

    if G is None:
        # Se o grafo não foi carregado (por exemplo, arquivo não encontrado ou erro)
        supported_types = ", ".join(GRAPH_FILENAMES.keys())
        if network_type not in GRAPH_FILENAMES:
             return JsonResponse({'error': f'Invalid network type: {network_type}. Supported types are: {supported_types}.'}, status=400)
        else:
             return JsonResponse({'error': f'Graph data for {network_type} not loaded on server. Please check server logs.'}, status=500)

    if request.method == 'GET':
        try:
            start_lat_str = request.GET.get('start_lat')
            start_lon_str = request.GET.get('start_lon')
            end_lat_str = request.GET.get('end_lat')
            end_lon_str = request.GET.get('end_lon')

            if not all([start_lat_str, start_lon_str, end_lat_str, end_lon_str]):
                return JsonResponse({'error': 'Missing one or more latitude/longitude parameters.'}, status=400)

            start_lat = float(start_lat_str)
            start_lon = float(start_lon_str)
            end_lat = float(end_lat_str)
            end_lon = float(end_lon_str)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid latitude/longitude parameters. Must be numbers.'}, status=400)

        try:
            # Chama a função de serviço para encontrar o caminho
            path_data = find_shortest_path(G, start_lat, start_lon, end_lat, end_lon)

            return JsonResponse({
                'message': 'Route found successfully!',
                'start_point': {'lat': start_lat, 'lon': start_lon, 'nearest_node_osmid': path_data['start_node_osmid']},
                'end_point': {'lat': end_lat, 'lon': end_lon, 'nearest_node_osmid': path_data['end_node_osmid']},
                'path_coordinates': path_data['path_coordinates'],
                'total_length_meters': path_data['total_length_meters']
            })

        except nx.NetworkXNoPath as e:
            return JsonResponse({'error': str(e)}, status=404)
        except nx.NodeNotFound as e:
            return JsonResponse({'error': str(e)}, status=404)
        except Exception as e:
            print(f"Error during pathfinding: {type(e).__name__} - {e}")
            return JsonResponse({'error': f'An unexpected error occurred during pathfinding: {str(e)}'}, status=500)

    else:
        return JsonResponse({'error': 'This endpoint only supports GET requests.'}, status=405)