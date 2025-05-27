import os
import osmnx as ox
import networkx as nx
from django.conf import settings
from django.http import JsonResponse

# Carregar o grafo 
# Idealmente, carregar uma vez na inicialização do servidor ou de forma otimizada.
GRAPH_FILENAME = 'marica_drive.graphml' # Certifique-se que este é o nome do arquivo que você salvou
GRAPH_FILEPATH = os.path.join(settings.BASE_DIR, 'map_data', GRAPH_FILENAME)
G = None

try:
    if os.path.exists(GRAPH_FILEPATH):
        print(f"Attempting to load graph from: {GRAPH_FILEPATH}")
        G = ox.load_graphml(GRAPH_FILEPATH)
        # Garantir que os atributos de peso sejam do tipo correto (ex: float)
        for _u, _v, data in G.edges(data=True):
            if 'length' in data:
                data['length'] = float(data['length'])
            # Converta outros atributos de peso se você os tiver (ex: 'travel_time')
        print(f"Graph '{GRAPH_FILENAME}' loaded successfully with {len(G.nodes())} nodes and {len(G.edges())} edges.")
    else:
        print(f"Graph file not found at {GRAPH_FILEPATH}. Run 'manage.py fetch_map_data' first.")
        # Note that this function does not exist yet.
except Exception as e:
    print(f"Error loading graph during app initialization: {e}")
    G = None # Garante que G é None se o carregamento falhar

# @api_view(['GET']) # Se fosse usar DRF e quisesse apenas requisições GET
def pathfinder_view(request):
    if G is None:
        return JsonResponse({'error': 'Graph data not loaded on server. Please check server logs.'}, status=500)

    if request.method == 'GET':
        # ... (lógica para obter start_lat, start_lon, end_lat, end_lon como antes) ...
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
            start_node_osmid = ox.nearest_nodes(G, X=start_lon, Y=start_lat)
            end_node_osmid = ox.nearest_nodes(G, X=end_lon, Y=end_lat)

            shortest_path_osmids = nx.dijkstra_path(G, source=start_node_osmid, target=end_node_osmid, weight='length')
            path_length_meters = nx.dijkstra_path_length(G, source=start_node_osmid, target=end_node_osmid, weight='length')

            # MODIFICAÇÃO AQUI para obter geometria detalhada das arestas
            path_coordinates = []
            if shortest_path_osmids and len(shortest_path_osmids) > 0:
                # Adicionar a coordenada do primeiro nó
                first_node_data = G.nodes[shortest_path_osmids[0]]
                path_coordinates.append({'lat': first_node_data['y'], 'lon': first_node_data['x']})

                # Iterar pelas arestas do caminho
                for i in range(len(shortest_path_osmids) - 1):
                    u = shortest_path_osmids[i]
                    v = shortest_path_osmids[i+1]
                    
                    # Arestas em um MultiDiGraph são identificadas por (u, v, key)
                    # Geralmente a chave 0 é a que queremos se não houver múltiplas arestas paralelas
                    # ou se a simplificação do OSMnx já lidou com isso.
                    # Se ox.settings.all_oneway=True foi usado, as arestas são únicas.
                    edge_data = G.get_edge_data(u, v)

                    if edge_data:
                        # Se houver múltiplas arestas entre u e v (comum em MultiDiGraph),
                        # pegue a primeira (key=0) ou a que tem o atributo 'length'
                        # (Dijkstra já escolheu a aresta ótima baseada no peso 'length').
                        # A chave pode variar, mas para um caminho de Dijkstra, geralmente há uma aresta específica.
                        # Vamos assumir que a primeira aresta encontrada (key=0) é a relevante do caminho.
                        # Em grafos simplificados e direcionados (all_oneway=True), geralmente só haverá uma ou nenhuma.
                        
                        # Tentativa de pegar a primeira chave se for um MultiGraph
                        if G.is_multigraph():
                             # Para um caminho de Dijkstra, esperamos que ele tenha usado a aresta com menor peso.
                             # Precisamos encontrar a aresta específica que Dijkstra usou se houver múltiplas.
                             # No entanto, para simplificar, se o atributo 'geometry' está na primeira (key 0), usamos.
                             # Uma abordagem mais robusta envolveria armazenar as arestas (u,v,key) do caminho.
                             # Por ora, vamos tentar a chave 0, que é comum.
                             key = 0 # Suposição comum
                             edge_data_specific = G.get_edge_data(u,v,key)
                             if edge_data_specific is None and len(edge_data)>0: # Se a chave 0 não funcionar, mas existe edge_data
                                 edge_data_specific = edge_data[next(iter(edge_data))] # Pega a primeira disponível
                        else: # Grafo não-multi
                            edge_data_specific = edge_data 


                        if edge_data_specific and 'geometry' in edge_data_specific:
                            # A geometria é um objeto LineString do Shapely
                            # Pegamos as coordenadas (lon, lat) e invertemos para (lat, lon)
                            xs, ys = edge_data_specific['geometry'].xy
                            # Adicionamos todas as coordenadas da geometria da aresta,
                            # *exceto a primeira* (pois já foi adicionada pelo nó anterior ou é o primeiro nó)
                            for j in range(1, len(xs)): # Começa do índice 1
                                path_coordinates.append({'lat': ys[j], 'lon': xs[j]})
                        else:
                            # Fallback: se não houver geometria, apenas adiciona o nó final da aresta
                            # (comportamento anterior)
                            end_node_data = G.nodes[v]
                            path_coordinates.append({'lat': end_node_data['y'], 'lon': end_node_data['x']})
                    else: # Fallback se get_edge_data não retornar nada (improvável para um caminho válido)
                        end_node_data = G.nodes[v]
                        path_coordinates.append({'lat': end_node_data['y'], 'lon': end_node_data['x']})
            
            return JsonResponse({
                'message': 'Route found successfully!',
                'start_point': {'lat': start_lat, 'lon': start_lon, 'nearest_node_osmid': start_node_osmid},
                'end_point': {'lat': end_lat, 'lon': end_lon, 'nearest_node_osmid': end_node_osmid},
                # 'path_osmids': shortest_path_osmids, # Pode manter se for útil para depuração
                'path_coordinates': path_coordinates,
                'total_length_meters': round(path_length_meters, 2)
            })

        # ... (blocos except como antes) ...
        except nx.NetworkXNoPath:
            return JsonResponse({'error': f'No path found between the nearest nodes ({start_node_osmid} and {end_node_osmid}). The locations might be in disconnected parts of the graph.'}, status=404)
        except nx.NodeNotFound:
            return JsonResponse({'error': 'Could not find one of the snapped start/end nodes in the graph.'}, status=404)
        except Exception as e:
            print(f"Error during pathfinding: {type(e).__name__} - {e}")
            return JsonResponse({'error': f'An unexpected error occurred during pathfinding: {str(e)}'}, status=500)

    else:
        return JsonResponse({'error': 'This endpoint only supports GET requests.'}, status=405)