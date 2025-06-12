import osmnx as ox
import networkx as nx
import copy

# Dicionário de condições (temporário. Seria melhor uma tabela na database.)
VARIABLE_CONDITIONS = { ... } 

# Esse cara age como fallback agora.
def get_average_speed_kmh(network_type: str):
    if network_type == 'drive':
        return 50  # km/h 
    elif network_type == 'bike':
        return 15  # km/h
    elif network_type == 'walk':
        return 5   # km/h
    return 10  # padrão. Especialmente se for anomalias da natureza como o 'all'.

# Modificar o shortest_path para receber length ou time (c/ condições variáveis de peso)
def find_path(G, start_lat, start_lon, end_lat, end_lon, network_type, optimize_for='length', average_speed_kmh=None):
    """
    Encontra um caminho otimizado entre dois pontos.

    Args:
        G: O grafo OSMnx carregado.
        start_lat: Latitude do ponto de início.
        start_lon: Longitude do ponto de início.
        end_lat: Latitude do ponto de fim.
        end_lon: Longitude do ponto de fim.
        network_type: Tipo de rede (ex: 'drive', 'bike', 'walk', 'all').
        average_speed_kmh: Velocidade média em km/h (opcional, sobrescreve network_type se fornecida).
        optimize_for: O critério de otimização. Pode ser 'length' (mais curto) ou 'time' (mais rápido, usando condições de variação de peso).
    Returns:
        Um dicionário contendo as coordenadas do caminho, o comprimento total e o tempo estimado,
        ou levanta uma exceção se o caminho não for encontrado ou ocorrer um erro.
    """

    # 1. Fazer cópia do grafo original para aplicar condições de variação de peso
    graph_copy = copy.deepcopy(G)

    # pegar a velociedad
    speed_kmh = average_speed_kmh or get_average_speed_kmh(network_type)
    speed_m_s = (speed_kmh * 1000) / 3600

    # 2. Adicionar os pesos das condições variáveis (se otimizando por tempo)
    affected_segments_info = {} # Dicionário para rastrear as condições aplicadas

    if optimize_for == 'time':
        # Adicionar o custo base 'travel_time' a todas as arestas
        for u, v, data in graph_copy.edges(data=True):
            data['travel_time'] = data['length'] / speed_m_s

        # Aplicar as penalidades das condições variáveis
        for condition_name, condition_data in VARIABLE_CONDITIONS.items():
            for u, v in condition_data['edges']:
                if graph_copy.has_edge(u, v):
                    # Multiplicar o tempo de viagem pelo fator de penalidade
                    # Acessar a primeira chave em um MultiDiGraph
                    key = 0 # ou a chave correta se houver múltiplas arestas
                    graph_copy[u][v][key]['travel_time'] *= condition_data['penalty_factor']
                    
                    # Guardar a informação para o frontend
                    affected_segments_info[(u, v, key)] = {
                        "condition": condition_name, 
                        "description": condition_data['description']
                    }

    # 3. Selecionar o atributo de peso
    weight_attribute = 'travel_time' if optimize_for == 'time' else 'length'

    try:
        # 1. Quando o usuário entrega uma série de coordenadas, OSMnx precisa determinar de qual NÓ essa coordenada se refere.
        # Pare para pensar: mesmo que um nó guarde sua coordenada, ela nunca é EXATA.
        start_node = ox.nearest_nodes(graph_copy, X=start_lon, Y=start_lat)
        end_node = ox.nearest_nodes(graph_copy, X=end_lon, Y=end_lat)

        # 2. O tópico principal: dijkstra_path é o algoritmo de Dijkstra.
        # Aqui, ele retorna um grafo. Um grafo que é, completamente inelegível pelo frontend, pois ele espera coordenadas.
        # Felizmente, há coordenadas aqui, mas precisam ser extraídas.
        shortest_path_nodes = nx.dijkstra_path(graph_copy, source=start_node, target=end_node, weight=weight_attribute)
        total_length_meters = nx.dijkstra_path_length(graph_copy, source=start_node, target=end_node, weight='length')

        # O tempo total agora deve ser calculado somando os 'travel_time' do caminho
        total_time_seconds = nx.dijkstra_path_length(graph_copy, source=start_node, target=end_node, weight='travel_time') if optimize_for == 'time' else (total_length_meters / speed_m_s)

        # Há uma ocasião comum para essa condiçaõ: o usuário tentou marcar uma área sem rota, ou seja, uma área não baixada.
        # Isso pode ser resolvido pela solução psicótica que é experimental_stitching, mas ela não foi implementada ainda.
        path_segments = []
        for i in range(len(shortest_path_nodes) - 1):
            u, v = shortest_path_nodes[i], shortest_path_nodes[i+1]
            key = 0 # Simplificação
            edge_data = graph_copy.get_edge_data(u, v, key)
            
            segment_info = {
                "start_node": u,
                "end_node": v,
                "coordinates": [],
                "length": edge_data['length'],
                "travel_time_seconds": edge_data.get('travel_time', edge_data['length'] / speed_m_s),
                "applied_condition": affected_segments_info.get((u, v, key)) # Adiciona info da condição, se houver
            }
            
            # Extrair coordenadas da geometria da aresta
            if 'geometry' in edge_data:
                xs, ys = edge_data['geometry'].xy
                segment_info['coordinates'] = [{'lat': y, 'lon': x} for y, x in zip(ys, xs)]
            else: # Fallback para nós
                segment_info['coordinates'] = [
                    {'lat': graph_copy.nodes[u]['y'], 'lon': graph_copy.nodes[u]['x']},
                    {'lat': graph_copy.nodes[v]['y'], 'lon': graph_copy.nodes[v]['x']}
                ]
            path_segments.append(segment_info)

        return {
            'optimize_for': optimize_for,
            'total_length_meters': round(total_length_meters, 2),
            'total_time_minutes': round(total_time_seconds / 60, 2),
            'path_segments': path_segments
        }

    except nx.NetworkXNoPath:
        raise nx.NetworkXNoPath("Nenhum caminho encontrado.")
    except Exception as e:
        raise Exception(f"Erro inesperado: {e}")
