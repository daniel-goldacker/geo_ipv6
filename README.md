# Geo IPv6 API
API em Python para consultar geolocalizacao de um endereco IPv6 com fallback entre provedores externos.

## Stack
- FastAPI
- Uvicorn
- Requests

## Requisitos
- Python 3.10+

## Instalacao
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Executar API
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

## Swagger e OpenAPI
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Se quiser regenerar o contrato:
```bash
python export_openapi.py
```

## Endpoints
### `GET /health`
Health check da API.

Exemplo de resposta:
```json
{
  "status": "ok"
}
```

### `GET /geo/{ip}`
Consulta geolocalizacao para um IPv6.

Exemplo:
```bash
curl http://localhost:8000/geo/2001:4860:4860::8888
```

### `GET /geo?ip={ipv6}` (recomendado)
Consulta geolocalizacao para um IPv6 via query param.

Exemplo:
```bash
curl "http://localhost:8000/geo?ip=2001:4860:4860::8888"
```

Exemplo de resposta:
```json
{
  "ip": "2001:4860:4860::8888",
  "provider": "ipapi",
  "data": {
    "ip": "2001:4860:4860::8888"
  }
}
```

## Codigos de erro
- `400`: IPv6 invalido ou IP nao e IPv6.
- `502`: Falha ao consultar provedores externos.

## Estrutura
- `geo_ipv6.py`: regra de negocio e fallback entre provedores.
- `api.py`: endpoints FastAPI.
- `export_openapi.py`: gera `openapi.json`.
