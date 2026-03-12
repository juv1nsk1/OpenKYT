import requests

async def check_address_forensics(address: str):
    response = requests.get(f"https://api.nowa.sh/checkaddress/{address}")
    if response.status_code == 200:
        return response.json()
    else:
        return {
            "address": address,
            "risk_score": None,
            "risk_level": "Unknown",
            "flags": []
        }


