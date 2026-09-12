from __future__ import annotations

import asyncio, ipaddress, os, re, secrets, socket
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

VERSION = "3.1.0"
API_KEY = os.getenv("RUDRA_API_KEY", "").strip()
TIMEOUT = 10.0

app = FastAPI(
    title="HiTech Free API",
    version=VERSION,
    description="Protected public-data and validation API",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

PUBLIC_ACTIONS = {
    "email_info", "vehicle_info", "ifsc_info", "gst_info", "pan_info", "ip_info",
    "pincode", "free_fire_info", "url_info", "dns_info", "domain_info",
    "phone_validate", "username_check", "headers_info", "port_check",
    "reverse_dns", "asn_info", "timezone_info", "text_extract",
}
DISABLED_PRIVATE = {
    "truecaller", "num_info", "aadhar_info", "family_info", "tg_to_num",
    "pak_no_info", "pak_cnic_info", "aadhar_to_pan_mask", "aadhar_to_bank",
}
ALL_ACTIONS = PUBLIC_ACTIONS | DISABLED_PRIVATE


class QueryRequest(BaseModel):
    action: str = Field(min_length=1, max_length=64)
    query: str = Field(min_length=1, max_length=500)


class APIResponse(BaseModel):
    success: bool
    action: str
    query: str
    data: Any | None = None
    error: str | None = None


async def require_key(request: Request) -> None:
    if not API_KEY:
        raise HTTPException(
            status_code=503,
            detail="API key is not configured. Set RUDRA_API_KEY in Vercel Environment Variables.",
        )
    supplied = request.headers.get("x-api-key") or request.query_params.get("key")
    if not supplied or not secrets.compare_digest(supplied, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


async def get_json(url: str, **kwargs: Any) -> Any:
    async with httpx.AsyncClient(
        timeout=TIMEOUT,
        follow_redirects=True,
        headers={
            "User-Agent": f"HiTech-Free-API/{VERSION}",
            "Accept": "application/json",
        },
    ) as client:
        response = await client.get(url, **kwargs)
        response.raise_for_status()
        return response.json()


async def head(url: str) -> dict[str, Any]:
    async with httpx.AsyncClient(
        timeout=TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": f"HiTech-Free-API/{VERSION}"},
    ) as client:
        response = await client.head(url)
        return {
            "status_code": response.status_code,
            "final_url": str(response.url),
            "headers": dict(response.headers),
        }


def ip_ok(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def domain_ok(value: str) -> bool:
    value = value.strip().lower().rstrip(".")
    return bool(
        re.fullmatch(
            r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}",
            value,
        )
    )


def url_ok(value: str) -> bool:
    return bool(re.fullmatch(r"https?://[^\s]+", value.strip(), re.I))


async def ip_info(query: str):
    if not ip_ok(query):
        raise ValueError("Invalid IP address")
    data = await get_json(f"https://ipwho.is/{query}")
    if data.get("success") is False:
        raise ValueError(data.get("message", "IP lookup failed"))
    return {
        key: data.get(key)
        for key in [
            "ip", "type", "continent", "country", "country_code", "region",
            "city", "latitude", "longitude", "postal", "timezone", "connection",
        ]
    }


async def pincode(query: str):
    if not re.fullmatch(r"\d{6}", query):
        raise ValueError("Indian pincode must contain 6 digits")
    data = await get_json(f"https://api.postalpincode.in/pincode/{query}")
    first = data[0] if data else {}
    return {
        "status": first.get("Status"),
        "message": first.get("Message"),
        "post_offices": first.get("PostOffice") or [],
    }


async def ifsc_info(query: str):
    query = query.upper().strip()
    if not re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", query):
        raise ValueError("Invalid IFSC format")
    data = await get_json(f"https://ifsc.razorpay.com/{query}")
    return {key: data.get(key) for key in ["IFSC", "BANK", "BRANCH", "CENTRE", "DISTRICT", "STATE", "ADDRESS", "CITY"]}


async def gst_info(query: str):
    query = query.upper().strip()
    if not re.fullmatch(r"\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]", query):
        raise ValueError("Invalid GSTIN format")
    states = {
        "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh",
        "05": "Uttarakhand", "06": "Haryana", "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
        "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur",
        "15": "Mizoram", "16": "Tripura", "17": "Meghalaya", "18": "Assam", "19": "West Bengal",
        "20": "Jharkhand", "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh",
        "24": "Gujarat", "27": "Maharashtra", "29": "Karnataka", "30": "Goa", "32": "Kerala",
        "33": "Tamil Nadu", "36": "Telangana", "37": "Andhra Pradesh",
    }
    return {
        "gstin": query,
        "state_code": query[:2],
        "state": states.get(query[:2], "Unknown"),
        "pan_segment": query[2:12],
        "entity_number": query[12],
        "checksum": query[-1],
        "format_valid": True,
    }


async def email_info(query: str):
    query = query.lower().strip()
    if not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", query):
        raise ValueError("Invalid email format")
    domain = query.rsplit("@", 1)[1]
    try:
        data = await get_json("https://dns.google/resolve", params={"name": domain, "type": "MX"})
        mx = [item.get("data") for item in data.get("Answer", []) if item.get("type") == 15]
    except Exception:
        mx = []
    return {"email": query, "domain": domain, "mx_present": bool(mx), "mx_records": mx}


async def dns_info(query: str):
    query = query.lower().strip().rstrip(".")
    if not domain_ok(query):
        raise ValueError("Invalid domain")
    records = {}
    for record_type in ["A", "AAAA", "MX", "NS", "TXT"]:
        try:
            data = await get_json("https://dns.google/resolve", params={"name": query, "type": record_type})
            records[record_type] = [item.get("data") for item in data.get("Answer", [])]
        except Exception:
            records[record_type] = []
    return {"domain": query, "records": records}


async def domain_info(query: str):
    query = query.lower().strip().rstrip(".")
    if not domain_ok(query):
        raise ValueError("Invalid domain")
    try:
        addresses = socket.getaddrinfo(query, 443, type=socket.SOCK_STREAM)
        ips = sorted({item[4][0] for item in addresses})
    except socket.gaierror:
        ips = []
    return {"domain": query, "resolved_ips": ips, "resolves": bool(ips)}


async def reverse_dns(query: str):
    if not ip_ok(query):
        raise ValueError("Invalid IP")
    try:
        hostname, aliases, addresses = socket.gethostbyaddr(query)
        return {"ip": query, "hostname": hostname, "aliases": aliases, "addresses": addresses}
    except socket.herror:
        return {"ip": query, "hostname": None, "aliases": [], "addresses": []}


async def url_info(query: str):
    if not url_ok(query):
        raise ValueError("URL must begin with http:// or https://")
    return {"url": query, **await head(query)}


async def headers_info(query: str):
    if not url_ok(query):
        raise ValueError("Invalid URL")
    result = await head(query)
    wanted = {
        "server", "content-type", "content-length", "location", "strict-transport-security",
        "content-security-policy", "x-frame-options", "x-content-type-options", "referrer-policy",
        "permissions-policy", "cache-control",
    }
    return {
        "status_code": result["status_code"],
        "final_url": result["final_url"],
        "security_headers": {
            key: value for key, value in result["headers"].items() if key.lower() in wanted
        },
    }


async def phone_validate(query: str):
    value = re.sub(r"[^\d+]", "", query)
    digits = value[3:] if value.startswith("+91") else value
    valid = bool(re.fullmatch(r"[6-9]\d{9}", digits))
    return {
        "valid": valid,
        "country": "India",
        "normalized": f"+91{digits}" if valid else None,
        "note": "Validation only; no owner or private-record lookup.",
    }


async def username_check(query: str):
    username = query.strip().lstrip("@")
    valid = bool(re.fullmatch(r"[A-Za-z0-9._-]{2,30}", username))
    return {
        "username": username,
        "format_valid": valid,
        "public_profile_urls": {
            "github": f"https://github.com/{username}",
            "reddit": f"https://www.reddit.com/user/{username}/",
        } if valid else {},
    }


async def vehicle_info(query: str):
    value = query.upper().strip().replace("-", " ")
    valid = bool(re.fullmatch(r"[A-Z]{2}\s?\d{1,2}\s?[A-Z]{0,3}\s?\d{1,4}", value))
    return {"registration": value, "format_valid": valid, "note": "Format validation only; no owner/address lookup."}


async def pan_info(query: str):
    value = query.upper().strip()
    valid = bool(re.fullmatch(r"[A-Z]{5}\d{4}[A-Z]", value))
    return {"pan": value, "format_valid": valid, "note": "Format validation only; no owner/tax-record lookup."}


async def free_fire_info(query: str):
    value = query.strip()
    valid = bool(re.fullmatch(r"\d{5,15}", value))
    return {"uid": value, "format_valid": valid, "note": "UID format validation only; no account extraction."}


async def port_check(query: str):
    match = re.fullmatch(r"([A-Za-z0-9.-]+):(\d{1,5})", query.strip())
    if not match:
        raise ValueError("Use host:port format")
    host, port = match.group(1), int(match.group(2))
    if not 1 <= port <= 65535:
        raise ValueError("Invalid port")
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=3)
        writer.close()
        await writer.wait_closed()
        return {"host": host, "port": port, "reachable": True}
    except Exception as exc:
        return {"host": host, "port": port, "reachable": False, "error": type(exc).__name__}


async def asn_info(query: str):
    data = await ip_info(query)
    connection = data.get("connection") or {}
    return {
        "ip": query,
        "asn": connection.get("asn"),
        "isp": connection.get("isp"),
        "organization": connection.get("org"),
        "domain": connection.get("domain"),
    }


async def timezone_info(query: str):
    data = await ip_info(query)
    timezone_data = data.get("timezone") or {}
    return {
        "ip": query,
        "timezone": timezone_data.get("id"),
        "utc": timezone_data.get("utc"),
        "current_time": timezone_data.get("current_time"),
    }


async def text_extract(query: str):
    return {
        "urls": sorted(set(re.findall(r"https?://[^\s]+", query, re.I))),
        "emails": sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", query))),
        "ipv4": sorted(set(re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", query))),
        "length": len(query),
    }


HANDLERS = {
    "ip_info": ip_info,
    "pincode": pincode,
    "ifsc_info": ifsc_info,
    "gst_info": gst_info,
    "email_info": email_info,
    "url_info": url_info,
    "dns_info": dns_info,
    "domain_info": domain_info,
    "phone_validate": phone_validate,
    "username_check": username_check,
    "headers_info": headers_info,
    "port_check": port_check,
    "reverse_dns": reverse_dns,
    "asn_info": asn_info,
    "timezone_info": timezone_info,
    "text_extract": text_extract,
    "vehicle_info": vehicle_info,
    "pan_info": pan_info,
    "free_fire_info": free_fire_info,
}


@app.get("/")
async def root():
    return {
        "name": "HiTech Free API",
        "version": VERSION,
        "status": "online",
        "authentication": "X-API-Key header or key query parameter",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
        "tools": "/tools",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "version": VERSION, "time": datetime.now(timezone.utc).isoformat()}


@app.get("/tools")
async def tools():
    return {
        "public_tools": sorted(PUBLIC_ACTIONS),
        "disabled_private": sorted(DISABLED_PRIVATE),
        "auth_required": True,
        "key_header": "X-API-Key",
    }


@app.get("/api/query", response_model=APIResponse)
async def query_get(
    request: Request,
    action: str = Query(..., min_length=1, max_length=64),
    query: str = Query(..., min_length=1, max_length=500),
):
    await require_key(request)
    return await run_query(action, query)


@app.post("/api/query", response_model=APIResponse)
async def query_post(request: Request, payload: QueryRequest):
    await require_key(request)
    return await run_query(payload.action, payload.query)


async def run_query(action: str, query: str):
    action = action.strip().lower()
    query = query.strip()
    if action not in ALL_ACTIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {action}. Use /tools.")
    if action in DISABLED_PRIVATE:
        return APIResponse(
            success=False,
            action=action,
            query=query,
            error="This action is disabled because it would access private identity/account records.",
        )
    try:
        return APIResponse(
            success=True,
            action=action,
            query=query,
            data=await HANDLERS[action](query),
        )
    except ValueError as exc:
        return APIResponse(success=False, action=action, query=query, error=str(exc))
    except httpx.HTTPError as exc:
        return APIResponse(
            success=False,
            action=action,
            query=query,
            error=f"Upstream request failed: {type(exc).__name__}",
        )
    except Exception as exc:
        return APIResponse(
            success=False,
            action=action,
            query=query,
            error=f"Internal error: {type(exc).__name__}",
        )
