import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ProxyConfig:
    def __init__(
        self,
        base_url: str = "geo.iproyal.com",
        port: str = "11200",
        username: str = "fEMMVG3irwJKw9cf",
        password: str = "mFpxOzaZBswDLOQ9",
        country: str = "mx",
        max_retries: int = 3,
        timeout: int = 10,
    ):
        self.base_url = base_url
        self.port = str(port)
        self.username = username
        self.password = password
        self.country = country
        self.max_retries = max_retries
        self.timeout = timeout

    def build_proxy_url(self) -> str:
        return (
            f"http://{self.username}:{self.password}_country-{self.country}@{self.base_url}:{self.port}"
        )


class ProxyManager:
    def __init__(self, config: ProxyConfig):
        self.config = config
        self._failed_proxies: Dict[str, datetime] = {}
        self._last_used: Optional[str] = None

    def _get_proxy_list(self) -> List[str]:
        proxy_url = self.config.build_proxy_url()
        return [proxy_url] * 3

    def get_proxy(self) -> Dict[str, str]:
        current_time = datetime.now()
        self._failed_proxies = {
            proxy: used_at
            for proxy, used_at in self._failed_proxies.items()
            if current_time - used_at < timedelta(minutes=5)
        }

        available = [p for p in self._get_proxy_list() if p not in self._failed_proxies]
        if not available:
            logger.warning("No hay proxies disponibles; reiniciando lista fallida")
            self._failed_proxies.clear()
            available = self._get_proxy_list()

        selected = random.choice([p for p in available if p != self._last_used] or available)
        self._last_used = selected
        logger.info(f"Proxy IPRoyal seleccionado: {selected}")
        return {"http": selected, "https": selected}

    def mark_failed(self, proxy_url: str) -> None:
        self._failed_proxies[proxy_url] = datetime.now()
        logger.warning(f"Proxy marcado como fallido: {proxy_url}")


proxy_manager = ProxyManager(
    ProxyConfig(
        base_url="geo.iproyal.com",
        port="11200",
        username="fEMMVG3irwJKw9cf",
        password="mFpxOzaZBswDLOQ9",
        country="mx",
    )
)


def get_rotating_proxy() -> Dict[str, str]:
    try:
        return proxy_manager.get_proxy()
    except Exception as exc:
        logger.error(f"Error al obtener proxy: {exc}")
        return {"http": None, "https": None}
