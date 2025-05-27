#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# (!) Solução temporária para o aviso do GDAL_DATA 
# Temporária, pois depende do manage.py. Isso não vai rodar em produção.
# Configure GDAL_DATA if not already set
if 'GDAL_DATA' not in os.environ:
    # Try common locations or use environment-specific detection
    import subprocess
    try:
        gdal_data = subprocess.check_output(['gdal-config', '--datadir'], text=True).strip()
        os.environ['GDAL_DATA'] = gdal_data
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback: let GDAL find its own data directory
        pass

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'queequeg.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
