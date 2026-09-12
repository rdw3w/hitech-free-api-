from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="HiTech Free API",
    version="1.1.0",
    description="Public-data OSINT and utility API. No private identity or credential lookup.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

TIMEOUT = 10.0
ACTIONS = {
    "ip_info", "pincode", "ifsc_info", "gst_info", "email_info", "url_info",
    "dns_info", "domain_info", "phone_validate", "username_check", "headers_info",
    "port_check", "reverse_dns", "asn_info", "timezone_info", "text_extract",
}


class QueryRequest(BaseModel):
    action: str = Field(min_length=1, max_length=64)
    query: str = Field(min_length=1, max_length=500)


class APIResponse(BaseModel):
    success: bool
    action: str
    query: str
    data: Any | None = None
    error: str | None = None


async def get_json(url: str, **kwargs: Any) -> Any:
    async with httpx.AsyncClient(
        timeout=TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": "HiTech-Free-API/1.1", "Accept": "application/json"},
    ) as client:
        response = await client.get(url, **kwargs)
        response.raise_for_status()
        return response.json()


async def head_request(url: str) -> dict[str, Any]:
    async with httpx.AsyncClient(
        timeout=TIMEOUT,
        follow_redirects=True,
        headers={"User-Agent": "HiTech-Free-API/1.1"},
    ) as client:
        response = await client.head(url)
        return {"status_code": response.status_code, "final_url": str(response.url), "headers": dict(response.headers)}


def valid_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def valid_domain(value: str) -> bool:
    return bool(re.fullmatch(r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", value.lower().strip()))


def valid_url(value: str) -> bool:
    return bool(re.fullmatch(r"https?://[^\s]+", value.strip(), re.I))


async def ip_info(q: str) -> dict[str, Any]:
    if not valid_ip(q): raise ValueError("Invalid IP address")
    data = await get_json(f"https://ipwho.is/{q}")
    if data.get("success") is False: raise ValueError(data.get("message", "IP lookup failed"))
    return {k: data.get(k) for k in ["ip", "type", "continent", "country", "country_code", "region", "city", "latitude", "longitude", "postal", "timezone", "connection"]}


async def pincode(q: str) -> dict[str, Any]:
    if not re.fullmatch(r"\d{6}", q): raise ValueError("Indian pincode must contain 6 digits")
    data = await get_json(f"https://api.postalpincode.in/pincode/{q}")
    first = data[0] if data else {}
    return {"status": first.get("Status"), "message": first.get("Message"), "post_offices": first.get("PostOffice") or []}


async def ifsc_info(q: str) -> dict[str, Any]:
    code = q.upper().strip()
    if not re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", code): raise ValueError("Invalid IFSC format")
    data = await get_json(f"https://ifsc.razorpay.com/{code}")
    return {k: data.get(k) for k in ["IFSC", "BANK", "BRANCH", "CENTRE", "DISTRICT", "STATE", "ADDRESS", "CITY"]}


async def gst_info(q: str) -> dict[str, Any]:
    gst = q.upper().strip()
    if not re.fullmatch(r"\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]", gst): raise ValueError("Invalid GSTIN format")
    states = {"01":"Jammu and Kashmir","02":"Himachal Pradesh","03":"Punjab","04":"Chandigarh","05":"Uttarakhand","06":"Haryana","07":"Delhi","08":"Rajasthan","09":"Uttar Pradesh","10":"Bihar","11":"Sikkim","12":"Arunachal Pradesh","13":"Nagaland","14":"Manipur","15":"Mizoram","16":"Tripura","17":"Meghalaya","18":"Assam","19":"West Bengal","20":"Jharkhand","21":"Odisha","22":"Chhattisgarh","23":"Madhya Pradesh","24":"Gujarat","27":"Maharashtra","29":"Karnataka","30":"Goa","32":"Kerala","33":"Tamil Nadu","36":"Telangana","37":"Andhra Pradesh"}
    return {"gstin": gst, "state_code": gst[:2], "state": states.get(gst[:2], "Unknown"), "pan_segment": gst[2:12], "entity_number": gst[12], "checksum": gst[-1], "format_valid": True}


async def email_info(q: str) -> dict[str, Any]:
    email = q.lower().strip()
    if not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", email): raise ValueError("Invalid email format")
    domain = email.rsplit("@", 1)[1]
    try:
        data = await get_json("https://dns.google/resolve", params={"name": domain, "type": "MX"})
        mx = [x.get("data") for x in data.get("Answer", []) if x.get("type") == 15]
    except Exception:
        mx = []
    return {"email": email, "domain": domain, "mx_present": bool(mx), "mx_records": mx}


async def dns_info(q: str) -> dict[str, Any]:
    domain = q.lower().strip()
    if not valid_domain(domain): raise ValueError("Invalid domain")
    result: dict[str, list[str]] = {}
    for record_type in ("A", "AAAA", "MX", "NS", "TXT"):
        try:
            data = await get_json("https://dns.google/resolve", params={"name": domain, "type": record_type})
            result[record_type] = [x.get("data") for x in data.get("Answer", [])]
        except Exception:
            result[record_type] = []
    return {"domain": domain, "records": result}


async def domain_info(q: str) -> dict[str, Any]:
    domain = q.lower().strip()
    if not valid_domain(domain): raise ValueError("Invalid domain")
    try:
        rows = socket.getaddrinfo(domain, 443, type=socket.SOCK_STREAM)
        ips = sorted({row[4][0] for row in rows})
    except socket.gaierror:
        ips = []
    return {"domain": domain, "resolved_ips": ips, "resolves": bool(ips)}


async def reverse_dns(q: str) -> dict[str, Any]:
    if not valid_ip(q): raise ValueError("Invalid IP")
    try:
        hostname, aliases, addresses = socket.gethostbyaddr(q)
        return {"ip": q, "hostname": hostname, "aliases": aliases, "addresses": addresses}
    except socket.herror:
        return {"ip": q, "hostname": None, "aliases": [], "addresses": []}


async def url_info(q: str) -> dict[str, Any]:
    if not valid_url(q): raise ValueError("URL must begin with http:// or https://")
    return {"url": q, **await head_request(q)}


async def headers_info(q: str) -> dict[str, Any]:
    if not valid_url(q): raise ValueError("Invalid URL")
    result = await head_request(q)
    wanted = {"server","content-type","content-length","location","strict-transport-security","content-security-policy","x-frame-options","x-content-type-options","referrer-policy","permissions-policy","cache-control"}
    return {"status_code": result["status_code"], "final_url": result["final_url"], "security_headers": {k:v for k,v in result["headers"].items() if k.lower() in wanted}}


async def phone_validate(q: str) -> dict[str, Any]:
    value = re.sub(r"[^\d+]", "", q)
    digits = value[3:] if value.startswith("+91") else value
    valid = bool(re.fullmatch(r"[6-9]\d{9}", digits))
    return {"valid": valid, "country": "India", "normalized": f"+91{digits}" if valid else None, "note": "Validation only; no owner, address, Aadhaar or private-record lookup."}


async def username_check(q: str) -> dict[str, Any]:
    username = q.strip().lstrip("@")
    valid = bool(re.fullmatch(r"[A-Za-z0-9._-]{2,30}", username))
    return {"username": username, "format_valid": valid, "public_profile_urls": {"github": f"https://github.com/{username}", "reddit": f"https://www.reddit.com/user/{username}/"} if valid else {}}


async def port_check(q: str) -> dict[str, Any]:
    match = re.fullmatch(r"([A-Za-z0-9.-]+):(\d{1,5})", q.strip())
    if not match: raise ValueError("Use host:port format")
    host, port = match.group(1), int(match.group(2))
    if not 1 <= port <= 65535: raise ValueError("Invalid port")
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout=3)
        writer.close(); await writer.wait_closed()
        return {"host": host, "port": port, "reachable": True}
    except Exception as exc:
        return {"host": host, "port": port, "reachable": False, "error": type(exc).__name__}


async def asn_info(q: str) -> dict[str, Any]:
    if not valid_ip(q): raise ValueError("Invalid IP")
    data = await get_json(f"https://ipwho.is/{q}")
    conn = data.get("connection") or {}
    return {"ip": q, "asn": conn.get("asn"), "isp": conn.get("isp"), "organization": conn.get("org"), "domain": conn.get("domain")}


async def timezone_info(q: str) -> dict[str, Any]:
    if not valid_ip(q): raise ValueError("Invalid IP")
    data = await get_json(f"https://ipwho.is/{q}")
    tz = data.get("timezone") or {}
    return {"ip": q, "timezone": tz.get("id"), "utc": tz.get("utc"), "current_time": tz.get("current_time")}


async def text_extract(q: str) -> dict[str, Any]:
    return {"urls": sorted(set(re.findall(r"https?://[^\s]+", q, re.I))), "emails": sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", q))), "ipv4": sorted(set(re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", q))), "length": len(q)}


HANDLERS = {"ip_info":ip_info,"pincode":pincode,"ifsc_info":ifsc_info,"gst_info":gst_info,"email_info":email_info,"url_info":url_info,"dns_info":dns_info,"domain_info":domain_info,"phone_validate":phone_validate,"username_check":username_check,"headers_info":headers_info,"port_check":port_check,"reverse_dns":reverse_dns,"asn_info":asn_info,"timezone_info":timezone_info,"text_extract":text_extract}


@app.get("/")
async def root() -> dict[str, Any]:
    return {"name":"HiTech Free API","version":"1.1.0","status":"online","docs":"/docs","openapi":"/openapi.json","endpoint":"POST /api/query","get_test":"GET /api/query?action=ip_info&query=8.8.8.8"}


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status":"ok","time":datetime.now(timezone.utc).isoformat()}


@app.get("/tools")
async def tools() -> dict[str, Any]:
    return {"tools":sorted(ACTIONS),"private_identity_lookup":False,"credential_lookup":False}


@app.get("/api/query", response_model=APIResponse)
async def query_api_get(action: str = Query(..., min_length=1, max_length=64), query: str = Query(..., min_length=1, max_length=500)) -> APIResponse:
    return await run_query(action, query)


@app.post("/api/query", response_model=APIResponse)
async def query_api(payload: QueryRequest) -> APIResponse:
    return await run_query(payload.action, payload.query)


async def run_query(action: str, query: str) -> APIResponse:
    action = action.strip().lower()
    query = query.strip()
    if action not in ACTIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported action: {action}. Use /tools for supported actions.")
    try:
        data = await HANDLERS[action](query)
        return APIResponse(success=True, action=action, query=query, data=data)
    except ValueError as exc:
        return APIResponse(success=False, action=action, query=query, error=str(exc))
    except httpx.HTTPError as exc:
        return APIResponse(success=False, action=action, query=query, error=f"Upstream request failed: {type(exc).__name__}")
    except Exception as exc:
        return APIResponse(success=False, action=action, query=query, error=f"Internal error: {type(exc).__name__}")
