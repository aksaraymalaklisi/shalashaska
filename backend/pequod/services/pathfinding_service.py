import osmnx as ox
import networkx as nx

# Isso assume valores hard-coded para os tipos de rede.
# O certo seria seria permitir uma configuração, provavelmente um parâmetro da função, recebido da API.
# Como o objetivo é entregar algo funcional e apresentável, será mantido assim, por qnaunto.
def get_average_speed_kmh(network_type):
    if network_type == 'drive':
        return 40  # km/h 
    elif network_type == 'bike':
        return 15  # km/h
    elif network_type == 'walk':
        return 5   # km/h
    return 10  # padrão

def find_shortest_path(G, start_lat, start_lon, end_lat, end_lon, network_type=None):
    """
    Encontra o caminho mais curto entre dois pontos em um grafo usando Dijkstra.

    Args:
        G: O grafo OSMnx carregado.
        start_lat: Latitude do ponto de início.
        start_lon: Longitude do ponto de início.
        end_lat: Latitude do ponto de fim.
        end_lon: Longitude do ponto de fim.
        network_type: Tipo de rede (ex: 'drive', 'bike', 'walk').

    Returns:
        Um dicionário contendo as coordenadas do caminho, o comprimento total e o tempo estimado,
        ou levanta uma exceção se o caminho não for encontrado ou ocorrer um erro.
    """
    try:
        start_node_osmid = ox.nearest_nodes(G, X=start_lon, Y=start_lat)
        end_node_osmid = ox.nearest_nodes(G, X=end_lon, Y=end_lat)

        shortest_path_osmids = nx.dijkstra_path(G, source=start_node_osmid, target=end_node_osmid, weight='length')
        path_length_meters = nx.dijkstra_path_length(G, source=start_node_osmid, target=end_node_osmid, weight='length')

        path_coordinates = []
        if shortest_path_osmids and len(shortest_path_osmids) > 0:
            # Adicionar a coordenada do primeiro nó
            first_node_data = G.nodes[shortest_path_osmids[0]]
            path_coordinates.append({'lat': first_node_data['y'], 'lon': first_node_data['x']})

            # Iterar pelas arestas do caminho
            for i in range(len(shortest_path_osmids) - 1):
                u = shortest_path_osmids[i]
                v = shortest_path_osmids[i+1]

                edge_data = G.get_edge_data(u, v)

                if edge_data:
                    if G.is_multigraph():
                         key = 0 # Suposição comum
                         edge_data_specific = G.get_edge_data(u,v,key)
                         if edge_data_specific is None and len(edge_data)>0:
                             edge_data_specific = edge_data[next(iter(edge_data))]
                    else:
                        edge_data_specific = edge_data


                    if edge_data_specific and 'geometry' in edge_data_specific:
                        xs, ys = edge_data_specific['geometry'].xy
                        for j in range(1, len(xs)):
                            path_coordinates.append({'lat': ys[j], 'lon': xs[j]})
                    else:
                        end_node_data = G.nodes[v]
                        path_coordinates.append({'lat': end_node_data['y'], 'lon': end_node_data['x']})
                else:
                    end_node_data = G.nodes[v]
                    path_coordinates.append({'lat': end_node_data['y'], 'lon': end_node_data['x']})

        # Calcular tempo estimado
        speed_kmh = get_average_speed_kmh(network_type) if network_type else 10
        speed_m_per_min = (speed_kmh * 1000) / 60
        estimated_time_minutes = round(path_length_meters / speed_m_per_min, 1)

        return {
            'start_node_osmid': start_node_osmid,
            'end_node_osmid': end_node_osmid,
            'path_coordinates': path_coordinates,
            'total_length_meters': round(path_length_meters, 2),
            'estimated_time_minutes': estimated_time_minutes
        }

    except nx.NetworkXNoPath:
        raise nx.NetworkXNoPath(f'No path found between the nearest nodes ({start_node_osmid} and {end_node_osmid}). The locations might be in disconnected parts of the graph.')
    except nx.NodeNotFound:
        raise nx.NodeNotFound('Could not find one of the snapped start/end nodes in the graph.')
    except Exception as e:
        raise Exception(f'An unexpected error occurred during pathfinding: {str(e)}')
