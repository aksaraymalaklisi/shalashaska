import os
import osmnx as ox
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Downloads map data from OpenStreetMap using OSMnx and saves it as GraphML.'

    def add_arguments(self, parser):
        parser.add_argument(
            'place_query', 
            type=str, 
            help='The place to download map data for (e.g., "Maricá, Rio de Janeiro, Brazil").'
        )
        parser.add_argument(
            '--filename',
            type=str,
            help='The filename to save the graph to (e.g., marica_drive_graph.graphml).',
            default='map_graph.graphml' # Nome de arquivo padrão
        )
        parser.add_argument(
            '--network-type',
            type=str,
            default='drive', # Tipos comuns: 'drive', 'walk', 'bike', 'all', 'all_private'
            help="The type of street network to download (e.g., 'drive', 'walk')."
        )

    def handle(self, *args, **options):
        place_query = options['place_query']
        filename = options['filename']
        network_type = options['network_type']

        # Define um diretório para salvar os dados do mapa, por exemplo, na raiz do projeto
        # ou em um diretório de 'data' dedicado.
        # Você pode querer configurar um caminho mais específico em seus settings.py
        BASE_DIR = getattr(settings, 'BASE_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        filepath = os.path.join(BASE_DIR, 'map_data', filename) # Salva em uma pasta 'map_data' na raiz

        # Cria o diretório 'map_data' se não existir
        os.makedirs(os.path.join(BASE_DIR, 'map_data'), exist_ok=True)

        self.stdout.write(self.style.NOTICE(f"Attempting to download '{network_type}' network for '{place_query}'..."))

        try:
            # 1. Baixar e construir o grafo com OSMnx
            #    Este objeto G já é um grafo NetworkX!
            G = ox.graph_from_place(place_query, network_type=network_type, retain_all=False, simplify=True)

            self.stdout.write(self.style.SUCCESS(f"Successfully downloaded graph with {len(G.nodes)} nodes and {len(G.edges)} edges."))

            # 2. (Opcional) Projetar o grafo para um CRS projetado (útil para algumas análises e visualizações)
            # G_projected = ox.project_graph(G)
            # self.stdout.write(self.style.NOTICE("Graph projected to UTM."))
            # Se for usar para cálculo de rotas com pesos de 'comprimento',
            # o OSMnx já adiciona o atributo 'length' (em metros) às arestas.

            # 3. Salvar o grafo como GraphML
            #    Usamos o G original (não projetado) se as coordenadas lat/lon forem mais úteis
            #    para integração com Leaflet depois. A projeção é mais para análise espacial precisa.
            ox.save_graphml(G, filepath=filepath)
            self.stdout.write(self.style.SUCCESS(f"Graph saved to {filepath}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
            self.stdout.write(self.style.WARNING("Ensure you have a working internet connection and the place query is valid."))
            self.stdout.write(self.style.WARNING("OSMnx can sometimes have issues with specific place queries or Overpass API availability."))