from __future__ import annotations

import asyncio, ipaddress, os, re, secrets, socket
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

VERSION = "3.0.0"
API_KEY = os.getenv("RUDRA_API_KEY", "")
TIMEOUT = 10.0

app = FastAPI(title="HiTech Free API", version=VERSION, description="Protected public-data and validation API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["GET","POST","OPTIONS"], allow_headers=["*"])

PUBLIC_ACTIONS = {
    "email_info","vehicle_info","ifsc_info","gst_info","pan_info","ip_info","pincode","free_fire_info",
    "url_info","dns_info","domain_info","phone_validate","username_check","headers_info","port_check",
    "reverse_dns","asn_info","timezone_info","text_extract"
}
DISABLED_PRIVATE = {
    "truecaller","num_info","aadhar_info","family_info","tg_to_num","pak_no_info","pak_cnic_info",
    "aadhar_to_pan_mask","aadhar_to_bank"
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
        raise HTTPException(status_code=503, detail="API key is not configured. Set RUDRA_API_KEY in Vercel environment variables.")
    supplied = request.headers.get("x-api-key") or request.query_params.get("key")
    if not supplied or not secrets.compare_digest(supplied, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

async def get_json(url: str, **kwargs: Any) -> Any:
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, headers={"User-Agent":f"HiTech-Free-API/{VERSION}","Accept":"application/json"}) as c:
        r = await c.get(url, **kwargs); r.raise_for_status(); return r.json()

async def head(url: str) -> dict[str,Any]:
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True, headers={"User-Agent":f"HiTech-Free-API/{VERSION}"}) as c:
        r = await c.head(url); return {"status_code":r.status_code,"final_url":str(r.url),"headers":dict(r.headers)}

def ip_ok(x:str)->bool:
    try: ipaddress.ip_address(x); return True
    except ValueError: return False

def domain_ok(x:str)->bool:
    x=x.strip().lower().rstrip('.')
    return bool(re.fullmatch(r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}",x))

def url_ok(x:str)->bool: return bool(re.fullmatch(r"https?://[^\s]+",x.strip(),re.I))

async def ip_info(q):
    if not ip_ok(q): raise ValueError("Invalid IP address")
    d=await get_json(f"https://ipwho.is/{q}")
    if d.get("success") is False: raise ValueError(d.get("message","IP lookup failed"))
    return {k:d.get(k) for k in ["ip","type","continent","country","country_code","region","city","latitude","longitude","postal","timezone","connection"]}
async def pincode(q):
    if not re.fullmatch(r"\d{6}",q): raise ValueError("Indian pincode must contain 6 digits")
    d=await get_json(f"https://api.postalpincode.in/pincode/{q}"); f=d[0] if d else {}
    return {"status":f.get("Status"),"message":f.get("Message"),"post_offices":f.get("PostOffice") or []}
async def ifsc_info(q):
    q=q.upper().strip()
    if not re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}",q): raise ValueError("Invalid IFSC format")
    d=await get_json(f"https://ifsc.razorpay.com/{q}")
    return {k:d.get(k) for k in ["IFSC","BANK","BRANCH","CENTRE","DISTRICT","STATE","ADDRESS","CITY"]}
async def gst_info(q):
    q=q.upper().strip()
    if not re.fullmatch(r"\d{2}[A-Z]{5}\d{4}[A-Z][A-Z0-9]Z[A-Z0-9]",q): raise ValueError("Invalid GSTIN format")
    states={"01":"Jammu and Kashmir","02":"Himachal Pradesh","03":"Punjab","04":"Chandigarh","05":"Uttarakhand","06":"Haryana","07":"Delhi","08":"Rajasthan","09":"Uttar Pradesh","10":"Bihar","11":"Sikkim","12":"Arunachal Pradesh","13":"Nagaland","14":"Manipur","15":"Mizoram","16":"Tripura","17":"Meghalaya","18":"Assam","19":"West Bengal","20":"Jharkhand","21":"Odisha","22":"Chhattisgarh","23":"Madhya Pradesh","24":"Gujarat","27":"Maharashtra","29":"Karnataka","30":"Goa","32":"Kerala","33":"Tamil Nadu","36":"Telangana","37":"Andhra Pradesh"}
    return {"gstin":q,"state_code":q[:2],"state":states.get(q[:2],"Unknown"),"pan_segment":q[2:12],"entity_number":q[12],"checksum":q[-1],"format_valid":True}
async def email_info(q):
    q=q.lower().strip()
    if not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+",q): raise ValueError("Invalid email format")
    dom=q.rsplit('@',1)[1]
    try:
        d=await get_json("https://dns.google/resolve",params={"name":dom,"type":"MX"}); mx=[x.get("data") for x in d.get("Answer",[]) if x.get("type")==15]
    except Exception: mx=[]
    return {"email":q,"domain":dom,"mx_present":bool(mx),"mx_records":mx}
async def dns_info(q):
    q=q.lower().strip().rstrip('.')
    if not domain_ok(q): raise ValueError("Invalid domain")
    out={}
    for t in ["A","AAAA","MX","NS","TXT"]:
        try:
            d=await get_json("https://dns.google/resolve",params={"name":q,"type":t}); out[t]=[x.get("data") for x in d.get("Answer",[])]
        except Exception: out[t]=[]
    return {"domain":q,"records":out}
async def domain_info(q):
    q=q.lower().strip().rstrip('.')
    if not domain_ok(q): raise ValueError("Invalid domain")
    try: ips=sorted({r[4][0] for r in socket.getaddrinfo(q,443,type=socket.SOCK_STREAM)})
    except socket.gaierror: ips=[]
    return {"domain":q,"resolved_ips":ips,"resolves":bool(ips)}
async def reverse_dns(q):
    if not ip_ok(q): raise ValueError("Invalid IP")
    try: h,a,ad=socket.gethostbyaddr(q); return {"ip":q,"hostname":h,"aliases":a,"addresses":ad}
    except socket.herror: return {"ip":q,"hostname":None,"aliases":[],"addresses":[]}
async def url_info(q):
    if not url_ok(q): raise ValueError("URL must begin with http:// or https://")
    return {"url":q,**await head(q)}
async def headers_info(q):
    if not url_ok(q): raise ValueError("Invalid URL")
    r=await head(q); wanted={"server","content-type","content-length","location","strict-transport-security","content-security-policy","x-frame-options","x-content-type-options","referrer-policy","permissions-policy","cache-control"}
    return {"status_code":r["status_code"],"final_url":r["final_url"],"security_headers":{k:v for k,v in r["headers"].items() if k.lower() in wanted}}
async def phone_validate(q):
    v=re.sub(r"[^\d+]","",q); digits=v[3:] if v.startswith('+91') else v; ok=bool(re.fullmatch(r"[6-9]\d{9}",digits))
    return {"valid":ok,"country":"India","normalized":f"+91{digits}" if ok else None,"note":"Validation only; no owner or private-record lookup."}
async def username_check(q):
    u=q.strip().lstrip('@'); ok=bool(re.fullmatch(r"[A-Za-z0-9._-]{2,30}",u))
    return {"username":u,"format_valid":ok,"public_profile_urls":{"github":f"https://github.com/{u}","reddit":f"https://www.reddit.com/user/{u}/"} if ok else {}}
async def vehicle_info(q):
    v=q.upper().strip().replace('-',' '); ok=bool(re.fullmatch(r"[A-Z]{2}\s?\d{1,2}\s?[A-Z]{0,3}\s?\d{1,4}",v))
    return {"registration":v,"format_valid":ok,"note":"Format validation only; no owner/address lookup."}
async def pan_info(q):
    v=q.upper().strip(); ok=bool(re.fullmatch(r"[A-Z]{5}\d{4}[A-Z]",v))
    return {"pan":v,"format_valid":ok,"note":"Format validation only; no owner/tax-record lookup."}
async def aadhar_info(q):
    v=re.sub(r"\s","",q); ok=bool(re.fullmatch(r"\d{12}",v))
    return {"format_valid":ok,"masked":"********"+v[-4:] if ok else None,"note":"Format/masking only; no identity lookup."}
async def free_fire_info(q):
    v=q.strip(); ok=bool(re.fullmatch(r"\d{5,15}",v)); return {"uid":v,"format_valid":ok,"note":"UID format validation only; no account extraction."}
async def port_check(q):
    m=re.fullmatch(r"([A-Za-z0-9.-]+):(\d{1,5})",q.strip())
    if not m: raise ValueError("Use host:port format")
    h,p=m.group(1),int(m.group(2))
    if not 1<=p<=65535: raise ValueError("Invalid port")
    try:
        _,w=await asyncio.wait_for(asyncio.open_connection(h,p),timeout=3); w.close(); await w.wait_closed(); return {"host":h,"port":p,"reachable":True}
    except Exception as e: return {"host":h,"port":p,"reachable":False,"error":type(e).__name__}
async def asn_info(q):
    d=await ip_info(q); c=d.get('connection') or {}; return {"ip":q,"asn":c.get('asn'),"isp":c.get('isp'),"organization":c.get('org'),"domain":c.get('domain')}
async def timezone_info(q):
    d=await ip_info(q); t=d.get('timezone') or {}; return {"ip":q,"timezone":t.get('id'),"utc":t.get('utc'),"current_time":t.get('current_time')}
async def text_extract(q):
    return {"urls":sorted(set(re.findall(r"https?://[^\s]+",q,re.I))),"emails":sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",q))),"ipv4":sorted(set(re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b",q))),"length":len(q)}

HANDLERS={"ip_info":ip_info,"pincode":pincode,"ifsc_info":ifsc_info,"gst_info":gst_info,"email_info":email_info,"url_info":url_info,"dns_info":dns_info,"domain_info":domain_info,"phone_validate":phone_validate,"username_check":username_check,"headers_info":headers_info,"port_check":port_check,"reverse_dns":reverse_dns,"asn_info":asn_info,"timezone_info":timezone_info,"text_extract":text_extract,"vehicle_info":vehicle_info,"pan_info":pan_info,"aadhar_info":aadhar_info,"free_fire_info":free_fire_info}

@app.get("/")
async def root(): return {"name":"HiTech Free API","version":VERSION,"status":"online","authentication":"x-api-key or key query parameter","docs":"/docs","health":"/health","tools":"/tools"}
@app.get("/health")
async def health(): return {"status":"ok","version":VERSION,"time":datetime.now(timezone.utc).isoformat()}
@app.get("/tools")
async def tools(): return {"public_tools":sorted(PUBLIC_ACTIONS),"disabled_private":sorted(DISABLED_PRIVATE),"auth_required":True}
@app.get("/api/query",response_model=APIResponse)
async def query_get(request:Request,action:str=Query(...,min_length=1,max_length=64),query:str=Query(...,min_length=1,max_length=500)):
    await require_key(request); return await run_query(action,query)
@app.post("/api/query",response_model=APIResponse)
async def query_post(request:Request,payload:QueryRequest):
    await require_key(request); return await run_query(payload.action,payload.query)

async def run_query(action,query):
    action=action.strip().lower(); query=query.strip()
    if action not in ALL_ACTIONS: raise HTTPException(status_code=400,detail=f"Unsupported action: {action}. Use /tools.")
    if action in DISABLED_PRIVATE: return APIResponse(success=False,action=action,query=query,error="This action is disabled because it would access private identity/account records.")
    try: return APIResponse(success=True,action=action,query=query,data=await HANDLERS[action](query))
    except ValueError as e: return APIResponse(success=False,action=action,query=query,error=str(e))
    except httpx.HTTPError as e: return APIResponse(success=False,action=action,query=query,error=f"Upstream request failed: {type(e).__name__}")
    except Exception as e: return APIResponse(success=False,action=action,query=query,error=f"Internal error: {type(e).__name__}")
