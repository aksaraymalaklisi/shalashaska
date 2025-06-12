import os
import osmnx as ox
import logging
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable
from django.conf import settings
from unidecode import unidecode
from threading import Lock

logger = logging.getLogger(__name__)
download_lock = Lock() # Essencial para evitar downloads duplicados em requisições simultâneas

# A gente precisa saber para onde o usuário está tentando ir e baixar o local daí, por isso o geopy.
# Isso é parte de uma função experimental.
def get_place_name_from_coords(lat, lon):
    """Descobre o nome do local (cidade, estado, país) a partir de coordenadas."""
    try:
        geolocator = Nominatim(user_agent="pathfinder_app")
        # O parâmetro 'addressdetails=True' e 'zoom=10' ajuda a obter o nome da cidade, aparentemente.
        location = geolocator.reverse((lat, lon), exactly_one=True, language='en', addressdetails=True, zoom=10)
        
        if location and 'address' in location.raw:
            address = location.raw['address']
            # Tenta obter a cidade ou algo equivalente.
            city = address.get('city') or address.get('town') or address.get('village')
            state = address.get('state')
            country = address.get('country')
            if city and state and country:
                # Retorna a query no formato usável para OSMnx.
                return f"{city}, {state}, {country}"
    except GeocoderUnavailable:
        logger.error("Serviço de geocodificação indisponível.")
    except Exception as e:
        logger.error(f"Erro na geocodificação reversa: {e}")
    return None

def get_map_key_and_filepath(place_prefix: str, network_type: str):
    """Gera a chave e o caminho do arquivo para um mapa."""
    key = f"{place_prefix}_{network_type}"
    map_data_dir = os.path.join(settings.BASE_DIR, 'map_data')
    os.makedirs(map_data_dir, exist_ok=True)
    filepath = os.path.join(map_data_dir, f"{key}.graphml")
    return key, filepath

def download_graph(place_query: str, place_prefix: str, network_type: str):
    """
    Baixa, salva e retorna um grafo.
    Esta função agora é o único lugar que lida com o download e salvamento.
    """
    key, filepath = get_map_key_and_filepath(place_prefix, network_type)

    # O Lock garante que se duas requisições chegarem ao mesmo tempo,
    # apenas uma fará o download, enquanto a outra espera.
    # Dito isso, o usuário é um demônio.
    # Ele dará um jeito.
    with download_lock:
        # Após adquirir o lock, verifica novamente se o arquivo já existe.
        # Pode ter sido baixado por outra requisição que estava na frente.
        if os.path.exists(filepath):
            logger.info(f"Mapa '{key}' já existe no disco. Carregando...")
            G = ox.load_graphml(filepath)
            return G

        try:
            logger.info(f"Iniciando download da rede '{network_type}' para '{place_query}'...")
            G = ox.graph_from_place(place_query, network_type=network_type, retain_all=False, simplify=True)
            ox.save_graphml(G, filepath=filepath)
            logger.info(f"Grafo para '{key}' salvo com sucesso em {filepath}")
            return G
        except Exception as e:
            logger.error(f"Falha ao baixar o grafo para '{key}': {e}")
            raise  # Re-lança a exceção para a view poder tratá-la.