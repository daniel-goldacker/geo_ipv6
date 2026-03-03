from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from geo_ipv6 import GeoLookupError, InvalidIPv6Error, lookup_geo_ipv6

app = FastAPI(
    title="Geo IPv6 API",
    description="API para consulta de geolocalização a partir de endereços IPv6.",
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


def _as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_coords(data: Dict[str, Any]) -> tuple[Optional[float], Optional[float]]:
    lat_candidates = (
        data.get("latitude"),
        data.get("lat"),
        data.get("location", {}).get("latitude")
        if isinstance(data.get("location"), dict)
        else None,
    )
    lon_candidates = (
        data.get("longitude"),
        data.get("lon"),
        data.get("lng"),
        data.get("location", {}).get("longitude")
        if isinstance(data.get("location"), dict)
        else None,
    )

    lat = next((parsed for parsed in (_as_float(v) for v in lat_candidates) if parsed is not None), None)
    lon = next((parsed for parsed in (_as_float(v) for v in lon_candidates) if parsed is not None), None)
    return lat, lon


class GeoMapResponse(BaseModel):
    ip: str = Field(..., examples=["2001:4860:4860::8888"])
    provider: str = Field(..., examples=["ipapi"])
    latitude: float
    longitude: float
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    raw: Dict[str, Any]


def _map_data_or_raise(ip: str) -> GeoMapResponse:
    geo = _lookup_or_raise(ip)
    lat, lon = _extract_coords(geo.data)
    if lat is None or lon is None:
        raise HTTPException(
            status_code=502,
            detail="Provedor retornou dados sem latitude/longitude para este IP.",
        )
    return GeoMapResponse(
        ip=geo.ip,
        provider=geo.provider,
        latitude=lat,
        longitude=lon,
        city=geo.data.get("city"),
        region=geo.data.get("region") or geo.data.get("region_name"),
        country=geo.data.get("country_name") or geo.data.get("country"),
        raw=geo.data,
    )


def _map_html(data: GeoMapResponse) -> str:
    popup = f"IP: {data.ip}<br>Provider: {data.provider}<br>Lat/Lon: {data.latitude:.6f}, {data.longitude:.6f}"
    map_script = f"""
    <link
      rel="stylesheet"
      href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
      crossorigin=""
    />
    <script
      src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
      integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
      crossorigin=""
    ></script>
    <script>
      const map = L.map("map").setView([{data.latitude}, {data.longitude}], 10);
      L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png", {{
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors"
      }}).addTo(map);
      L.marker([{data.latitude}, {data.longitude}]).addTo(map)
        .bindPopup(`{popup}`)
        .openPopup();
    </script>
    """

    return f"""
    <!doctype html>
    <html lang="pt-BR">
      <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Mapa IP {data.ip}</title>
        <style>
          body {{
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f6f8fa;
          }}
          header {{
            padding: 12px 16px;
            background: #111827;
            color: #fff;
            font-size: 14px;
          }}
          #map {{
            width: 100%;
            height: calc(100vh - 48px);
          }}
        </style>
      </head>
      <body>
        <header>
          IP: {data.ip} | Provedor Geo: {data.provider} | Mapa: Leaflet + OpenStreetMap
        </header>
        <div id="map"></div>
        {map_script}
      </body>
    </html>
    """
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
    summary="Consulta geolocalização por IPv6 (query param)",
)
def get_geo_ipv6_query(
    ip: str = Query(..., description="Endereço IPv6 para consulta"),
) -> GeoIpv6Response:
    return _lookup_or_raise(ip)


@app.get(
    "/geo/{ip}",
    response_model=GeoIpv6Response,
    responses={400: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    tags=["geo"],
    summary="Consulta geolocalização por IPv6 (rota legada)",
)
def get_geo_ipv6(ip: str) -> GeoIpv6Response:
    return _lookup_or_raise(ip)


@app.get(
    "/map",
    response_class=HTMLResponse,
    responses={400: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
    tags=["map"],
    summary="Retorna mapa interativo do IP (Leaflet + OpenStreetMap)",
)
def render_map(
    ip: str = Query(..., description="Endereco IPv6 para consulta"),
) -> HTMLResponse:
    map_data = _map_data_or_raise(ip)
    html = _map_html(map_data)
    return HTMLResponse(content=html)




