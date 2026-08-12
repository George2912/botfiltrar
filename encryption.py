import base64
import re

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding


PUBLIC_KEY_B64 = (
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0jZCD+Lzz2R4ivOZ0xnSeJxeqXNJrjR9fSz+Q363wds16rdYN0r67aDLy9jrXs7KQXR+SfSFBllK1/2HtK52492utHgsG+55R8Xfhf2FUtcrWEP+r+lAMJkBWqqIpIAwZjNCG1QfwpPiqomiyVAXQ2Fkw6bJpwUmKF7Y9rL0VTGUYHzy8S+JUDzbxpqBFwrT4A7GO4Cync++hESsapnnAC7rG6812ZwwNAszlAO3HpUi+LdlGcq9RHxuPHBbeln63ATovFZUGfWxMgNQMzp8I1hPepq+6f6z8prpB7uNrNp+/x/6C1HjLbOz8jk0qG3kGNoRMFYqIz5EBdsAlaz4qwIDAQAB"
)

PUBLIC_KEY_PEM = f"-----BEGIN PUBLIC KEY-----\n{PUBLIC_KEY_B64}\n-----END PUBLIC KEY-----"
PUBLIC_KEY = serialization.load_pem_public_key(PUBLIC_KEY_PEM.encode())


def encriptar_tarjeta(tarjeta: str) -> str:
    limpia = re.sub(r"[^0-9]", "", tarjeta)
    if len(limpia) != 16:
        raise ValueError("La tarjeta debe tener 16 dígitos")

    encrypted = PUBLIC_KEY.encrypt(limpia.encode("utf-8"), padding.PKCS1v15())
    return base64.b64encode(encrypted).decode("utf-8")


def encrypt_recovery_id(value: str) -> str:
    encrypted = PUBLIC_KEY.encrypt(value.encode("utf-8"), padding.PKCS1v15())
    return base64.b64encode(encrypted).decode("utf-8")


def encrypt_password(value: str) -> str:
    encrypted = PUBLIC_KEY.encrypt(value.encode("utf-8"), padding.PKCS1v15())
    return base64.b64encode(encrypted).decode("utf-8")
