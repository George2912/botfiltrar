import base64
import time
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend


PUBLIC_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0jZCD+Lzz2R4ivOZ0xnSeJxeqXNJrjR9fSz+Q363wds16rdYN0r67aDLy9jrXs7KQXR+SfSFBllK1/2HtK52492utHgsG+55R8Xfhf2FUtcrWEP+r+lAMJkBWqqIpIAwZjNCG1QfwpPiqomiyVAXQ2Fkw6bJpwUmKF7Y9rL0VTGUYHzy8S+JUDzbxpqBFwrT4A7GO4Cync++hESsapnnAC7rG6812ZwwNAszlAO3HpUi+LdlGcq9RHxuPHBbeln63ATovFZUGfWxMgNQMzp8I1hPepq+6f6z8prpB7uNrNp+/x/6C1HjLbOz8jk0qG3kGNoRMFYqIz5EBdsAlaz4qwIDAQAB"
APP_VERSION = "20260701.1"
MANUFACTURER = "Google"
ANDROID_VERSION = "16"
IS_SIMULATOR = False

_public_key_cache = None


def _load_public_key():
    global _public_key_cache
    if _public_key_cache is None:
        clean_key = PUBLIC_KEY.replace("\n", "").strip()
        der_bytes = base64.b64decode(clean_key)
        _public_key_cache = serialization.load_der_public_key(der_bytes, backend=default_backend())
    return _public_key_cache


def generate_x_device_hash(device_uuid: str) -> str:
    public_key = _load_public_key()
    timestamp = int(time.time() * 1000)
    platform_info = f"android/{ANDROID_VERSION};{MANUFACTURER};{APP_VERSION}"
    simulator_flag = "true" if IS_SIMULATOR else "false"
    payload = f"{device_uuid}|{platform_info}|{timestamp}|isSimulator:{simulator_flag}"
    encrypted = public_key.encrypt(payload.encode("utf-8"), padding.PKCS1v15())
    return base64.b64encode(encrypted).decode("utf-8")
