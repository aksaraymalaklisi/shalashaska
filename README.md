# O backend e frontend do aplicativo de rotas

## Rodando com Docker

O aplicativo pode ser inicializado com Docker.

Clone o repositório:
`git clone https://github.com/aksaraymalaklisi/shalashaska.git`

Execute:
`docker compose up -d --build`

A porta exposta será: 7777 para o backend e 8888 para o frontend.
Nesse caso, acesse a porta 8888.

## Rodando manualmente

### Backend

Você precisa ter conda instalado.

No diretório do backend, rode:
`conda env create -f environment.yml`

Ative a .env:
`conda activate shalashaska`

Faça migração:
`python manage.py migrate`

E rode o servidor:
`python manage.py runserver`

### Frontend

Você precisa ter Node.js instalado.

No diretório do frontend, rode:
`npm install`

E rode o servidor:
`npm run dev`

## A .env

Essas entradas não são obrigatórias para o funcionamento do aplicativo.
Atualmente, estas são as variáveis do arquivo .env, baseado na PR #2:

```bash
GDAL_DATA=<local_do_GDAL_DATA>
DJANGO_SECRET_KEY=<nova-chave-secreta>
DJANGO_DEBUG=<True ou False>
DJANGO_ALLOWED_HOSTS=<hosts>
OSMNX_PLACE_PREFIX=<prefixo_do_local_carregado>

VITE_API_HOST=<site_da_api>
```
