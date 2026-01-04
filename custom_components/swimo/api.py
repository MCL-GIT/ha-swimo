"""Client API Swimo - VERSION SIMPLIFIÉE
IMPORTANT: Copiez la version complète depuis l'artifact pour le support WebSocket complet
"""
import aiohttp
from datetime import datetime, timedelta
import logging

_LOGGER = logging.getLogger(__name__)

class SwimoAPI:
    BASE_URL = "https://socket.swimo.io/cgi-bin"
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.token = None
        self.token_expires = None
        self._session = None
        self._data = {}
        self._websocket_connected = False
    
    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def get_token(self) -> str:
        if self.token and self.token_expires and datetime.now() < self.token_expires:
            return self.token
        session = await self._get_session()
        headers = {"user": self.email, "code": self.password}
        try:
            async with session.get(f"{self.BASE_URL}/get_token", headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    self.token = data.get("token") or data.get("appid")
                    self.token_expires = datetime.now() + timedelta(days=29)
                    return self.token
        except Exception as e:
            _LOGGER.error(f"Erreur token: {e}")
        return None
    
    async def get_all_data(self) -> dict:
        token = await self.get_token()
        if not token:
            return self._data or {}
        session = await self._get_session()
        try:
            async with session.get(f"{self.BASE_URL}/get_all", headers={"appid": token}, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    self._data = await response.json()
                    return self._data
        except Exception as e:
            _LOGGER.error(f"Erreur données: {e}")
        return self._data or {}
    
    async def update_device(self, key: str, value: str, number: int = None) -> bool:
        token = await self.get_token()
        if not token:
            return False
        params = {"key": key, "value": value}
        if number is not None:
            params["number"] = number
        session = await self._get_session()
        try:
            async with session.get(f"{self.BASE_URL}/update_all", headers={"appid": token}, params=params) as response:
                return response.status == 200
        except:
            return False
    
    def get_sensors(self) -> list:
        return self._data.get("sensors", [])
    
    def get_devices(self) -> list:
        return self._data.get("devices", [])
    
    def get_actions(self) -> list:
        return self._data.get("actions", [])
    
    def get_system_info(self) -> dict:
        return self._data.get("system", {})
    
    async def start_websocket(self, callback=None):
        # TODO: Implémenter WebSocket - voir artifact complet
        return False
    
    def is_websocket_connected(self) -> bool:
        return self._websocket_connected
