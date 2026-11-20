
import logging
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ProxyConfig:
    def __init__(
        self,
        base_url="geo.iproyal.com",
        port="11200",
        username=None,
        password=None,
        country="mx",
        max_retries=3,
        timeout=20,
    ):
        self.base_url = base_url
        self.port = str(port)
        self.username = username or os.getenv("PROXY_USERNAME")
        self.password = password or os.getenv("PROXY_PASSWORD")
        self.country = country
        self.max_retries = max_retries
        self.timeout = timeout

    def build_proxy_url(self) -> str:
        if not self.username or not self.password:
            raise ValueError("Proxy no configurado")

        return (
            f"http://{self.username}:"
            f"{self.password}_country-{self.country}"
            f"@{self.base_url}:{self.port}"
        )


class ProxyManager:
    def __init__(self, config: ProxyConfig):
        self.config = config
        self._failed_proxies = {}
        self._last_used = None

    def _get_proxy_list(self) -> List[str]:
        # Un único endpoint: no representa tres proxies distintos.
        return [self.config.build_proxy_url()]

    def get_proxy(self) -> Dict[str, str]:
        current_time = datetime.now()

        self._failed_proxies = {
            proxy: failed_at
            for proxy, failed_at in self._failed_proxies.items()
            if current_time - failed_at < timedelta(minutes=5)
        }

        available = [
            p for p in self._get_proxy_list()
            if p not in self._failed_proxies
        ]

        if not available:
            raise RuntimeError("Proxy temporalmente no disponible")

        selected = random.choice(available)
        self._last_used = selected

        # Nunca registrar la URL ni las credenciales.
        logger.info("Proxy seleccionado correctamente")

        return {"http": selected, "https": selected}

    def mark_failed(self, proxy_url: str) -> None:
        self._failed_proxies[proxy_url] = datetime.now()
        logger.warning("Se detectó un proxy con errores de conexión")


proxy_manager = ProxyManager(
    ProxyConfig(
        base_url="geo.iproyal.com",
        port="11200",
        country="mx",
    )
)


def get_rotating_proxy() -> Optional[Dict[str, str]]:
    try:
        return proxy_manager.get_proxy()
    except Exception:
        logger.error("No se pudo obtener la configuración del proxy")
        return None
