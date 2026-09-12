# HiTech Free API

FastAPI-based public-data OSINT and utility API designed for Vercel.

## Features

- IP geolocation and network metadata
- India Post pincode lookup
- IFSC bank/branch lookup
- GSTIN format/state parsing
- Email domain/MX checks
- DNS records
- Domain resolution
- URL/HTTP metadata
- Security-header inspection
- Indian phone-number format validation
- Public username URL generation
- Reverse DNS
- ASN/ISP metadata
- IP timezone metadata
- Text extraction
- Single JSON API endpoint
- Swagger/OpenAPI docs

## Endpoint

`POST /api/query`

```json
{
  "action": "ip_info",
  "query": "8.8.8.8"
}
```

## Vercel

The repository contains `vercel.json` and `requirements.txt`. Import the repository into Vercel and deploy with the default Python runtime.

## Privacy boundary

This project intentionally does not provide Aadhaar-to-person, family, bank-account, private social-profile, credential, password, or other private-record lookup functionality. It uses public/non-sensitive metadata only.

## Local run

```bash
pip install -r requirements.txt
uvicorn api.index:app --reload
```

Then open `/docs`.
