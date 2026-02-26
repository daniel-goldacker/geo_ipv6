from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from geo_ipv6 import GeoLookupError, InvalidIPv6Error, lookup_geo_ipv6

app = FastAPI(
    title="Geo IPv6 API",
    description="API para consulta de geolocalizacao a partir de enderecos IPv6.",
    version="1.0.0",
)


class GeoIpv6Response(BaseModel):
    ip: str = Field(..., examples=["2001:4860:4860::8888"])
    provider: str = Field(..., examples=["ipapi"])
    data: Dict[str, Any]


class ErrorResponse(BaseModel):
    detail: str


def _lookup_or_raise(ip: str) -> GeoIpv6Response:
    try:
        provider, data = lookup_geo_ipv6(ip)
    except InvalidIPv6Error as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except GeoLookupError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return GeoIpv6Response(ip=ip, provider=provider, data=data)


@app.get(
    "/health",
    tags=["health"],
    summary="Health check",
)
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/geo",
    response_model=GeoIpv6Response,
    responses={400: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    tags=["geo"],
    summary="Consulta geolocalizacao por IPv6 (query param)",
)
def get_geo_ipv6_query(
    ip: str = Query(..., description="Endereco IPv6 para consulta"),
) -> GeoIpv6Response:
    return _lookup_or_raise(ip)


@app.get(
    "/geo/{ip}",
    response_model=GeoIpv6Response,
    responses={400: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    tags=["geo"],
    summary="Consulta geolocalizacao por IPv6 (rota legada)",
)
def get_geo_ipv6(ip: str) -> GeoIpv6Response:
    return _lookup_or_raise(ip)
