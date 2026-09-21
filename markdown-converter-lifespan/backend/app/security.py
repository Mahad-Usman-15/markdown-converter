import ipaddress, socket
from urllib.parse import urlsplit, urlunsplit, quote
from app.errors import ConversionError

def validate_url(value: str):
    try:
        if not value or len(value)>4096 or any(ord(c)<33 for c in value) or "\\" in value: raise ValueError()
        p = urlsplit(value)
        if p.scheme not in ("http", "https") or not p.hostname or p.username is not None or p.password is not None:
            raise ValueError()
        host = p.hostname.rstrip(".").encode("idna").decode("ascii").lower()
        port = p.port if p.port is not None else (443 if p.scheme == "https" else 80)
        if port != (443 if p.scheme == "https" else 80) or not host or host == "localhost" or host.endswith((".local", ".localhost", ".internal")):
            raise ValueError()
        return urlunsplit((p.scheme, f"[{host}]" if ":" in host else host,
            quote(p.path or "/", safe="/%:@!$&'()*+,;=-._~"),
            quote(p.query, safe="/%?:@!$&'()*+,;=-._~"), "")), host, port
    except (ValueError, UnicodeError):
        raise ConversionError("invalid_url", "Enter a public HTTP or HTTPS URL on a standard port.") from None

def resolve(host, port):
    try:
        addresses = list(dict.fromkeys(x[4][0] for x in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)))
    except OSError:
        raise ConversionError("dns_failed", "The website address could not be resolved.") from None
    for addr in addresses:
        ip = ipaddress.ip_address(addr)
        if ip.ipv4_mapped: ip = ip.ipv4_mapped
        if not ip.is_global or ip.is_multicast or ip.is_reserved:
            raise ConversionError("blocked_url", "Private and local network addresses are not supported.")
    if not addresses: raise ConversionError("dns_failed", "The website address could not be resolved.")
    return addresses[0]
