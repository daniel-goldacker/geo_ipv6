import ipaddress
from typing import Dict, Tuple

import requests


class InvalidIPv6Error(ValueError):
    pass


class GeoLookupError(RuntimeError):
    pass


def _validate_ipv6(ip: str) -> None:
    try:
        parsed = ipaddress.ip_address(ip)
    except ValueError as exc:
        raise InvalidIPv6Error("IPv6 invalido.") from exc
    if parsed.version != 6:
        raise InvalidIPv6Error("O endpoint aceita apenas IPv6.")


def lookup_geo_ipv6(ip: str, session: requests.Session | None = None) -> Tuple[str, Dict]:
    _validate_ipv6(ip)

    providers = [
        ("ipapi", f"https://ipapi.co/{ip}/json/"),
        ("ipwhois", f"https://ipwho.is/{ip}"),
    ]
    last_error = None
    http = session or requests.Session()

    try:
        for provider, url in providers:
            try:
                response = http.get(url, timeout=(3, 7))
                response.raise_for_status()
                data = response.json()

                if provider == "ipapi" and data.get("error"):
                    continue
                if provider == "ipwhois" and data.get("success") is False:
                    continue

                if data:
                    return provider, data
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
    finally:
        if session is None:
            http.close()

    raise GeoLookupError(
        "Nao foi possivel consultar geolocalizacao. "
        "Verifique DNS/internet ou troque o servidor DNS da maquina."
    ) from last_error


def geo_ipv6(ip: str) -> Dict:
    _, data = lookup_geo_ipv6(ip)
    return data
