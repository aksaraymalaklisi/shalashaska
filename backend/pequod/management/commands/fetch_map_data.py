import os
import osmnx as ox
from django.core.management.base import BaseCommand
from django.conf import settings


# Simplificar o comando e baixar novos tipos de redes
# O comando a seguir agora irá baixar três tipos de rede por padrão: 
# python manage.py fetch_map_data "Maricá, RJ, Brazil"
# ou você pode especificar com --network_types:
# python manage.py fetch_map_data "Maricá, RJ, Brazil" --network_types drive walk bike
class Command(BaseCommand):
    help = 'Downloads map data from OpenStreetMap for specified network types and saves them.'

    def add_arguments(self, parser):
        parser.add_argument('place_query', type=str, help='The place to download map data for.')
        # Novo argumento para especificar os tipos de rede, ou pode ser uma lista fixa
        parser.add_argument(
            '--network_types',
            nargs='+', # Aceita um ou mais argumentos
            default=['drive', 'walk', 'bike'], # Padrão para os três tipos
            help="Space-separated list of network types (e.g., 'drive' 'walk' 'bike')."
        )

    def handle(self, *args, **options):
        place_query = options['place_query']
        network_types_to_fetch = options['network_types']

        BASE_DIR = getattr(settings, 'BASE_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        map_data_dir = os.path.join(BASE_DIR, 'map_data')
        os.makedirs(map_data_dir, exist_ok=True)

        for nt in network_types_to_fetch:
            self.stdout.write(self.style.NOTICE(f"Attempting to download '{nt}' network for '{place_query}'..."))
            filename = f"marica_{nt.replace('_', '-')}.graphml" # Ex: marica_drive.graphml, marica_walk.graphml
            filepath = os.path.join(map_data_dir, filename)

            try:
                G = ox.graph_from_place(place_query, network_type=nt, retain_all=False, simplify=True)
                ox.save_graphml(G, filepath=filepath)
                self.stdout.write(self.style.SUCCESS(f"Graph for '{nt}' ({len(G.nodes)} nodes, {len(G.edges)} edges) saved to {filepath}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"An error occurred for network type '{nt}': {e}"))