# ============================================================================
# custom_components/swimo/api.py
# ============================================================================

import aiohttp
import asyncio
from datetime import datetime, timedelta
import logging
import socketio
import json

_LOGGER = logging.getLogger(__name__)

class SwimoAPI:
    """API client pour Swimo/Orkestron avec support WebSocket temps réel."""
    
    BASE_URL = "https://socket.swimo.io/cgi-bin"
    SOCK_URL = "https://sock.swimo.io"
    WSS_URL = "wss://now.swimo.io"
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.token = None
        self.token_expires = None
        self._session = None
        self._data = {}
        self._sio = None
        self._callbacks = []
        self._websocket_connected = False
        self._reconnect_task = None
    
    async def _get_session(self):
        """Récupère ou crée une session aiohttp."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """Ferme les connexions."""
        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
        
        if self._sio and self._websocket_connected:
            try:
                await self._sio.disconnect()
            except Exception as e:
                _LOGGER.debug(f"Erreur déconnexion WebSocket: {e}")
        
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def get_token(self) -> str:
        """Obtient un token valide."""
        if self.token and self.token_expires and datetime.now() < self.token_expires:
            return self.token
        
        session = await self._get_session()
        headers = {
            "user": self.email,
            "code": self.password
        }
        
        try:
            async with session.get(
                f"{self.BASE_URL}/get_token",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.token = data.get("token") or data.get("appid")
                    self.token_expires = datetime.now() + timedelta(days=29)
                    _LOGGER.info("Token Swimo obtenu avec succès")
                    return self.token
                else:
                    text = await response.text()
                    _LOGGER.error(f"Erreur {response.status}: {text}")
                    return None
        except Exception as e:
            _LOGGER.error(f"Exception lors de l'obtention du token: {e}")
            return None
    
    async def get_all_data(self) -> dict:
        """Récupère toutes les données du système."""
        token = await self.get_token()
        if not token:
            _LOGGER.error("Impossible d'obtenir un token valide")
            return self._data or {}
        
        session = await self._get_session()
        headers = {"appid": token}
        
        try:
            async with session.get(
                f"{self.BASE_URL}/get_all",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    self._data = await response.json()
                    _LOGGER.debug(f"Données récupérées: {len(self._data.get('sensors', []))} capteurs")
                    return self._data
                else:
                    text = await response.text()
                    _LOGGER.error(f"Erreur {response.status}: {text}")
                    return self._data or {}
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout lors de la récupération des données")
            return self._data or {}
        except Exception as e:
            _LOGGER.error(f"Exception lors de la récupération: {e}")
            return self._data or {}
    
    async def update_device(self, key: str, value: str, number: int = None) -> bool:
        """Met à jour un appareil ou paramètre."""
        token = await self.get_token()
        if not token:
            return False
        
        session = await self._get_session()
        headers = {"appid": token}
        params = {"key": key, "value": value}
        
        if number is not None:
            params["number"] = number
        
        try:
            async with session.get(
                f"{self.BASE_URL}/update_all",
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                success = response.status == 200
                if success:
                    _LOGGER.info(f"Mise à jour réussie: {key}={value}")
                else:
                    _LOGGER.error(f"Échec mise à jour: {response.status}")
                return success
        except Exception as e:
            _LOGGER.error(f"Exception lors de la mise à jour: {e}")
            return False
    
    async def get_sensors_realtime(self) -> dict:
        """Récupère les données des capteurs en temps réel via POST."""
        token = await self.get_token()
        if not token:
            return {}
        
        session = await self._get_session()
        
        try:
            async with session.post(
                self.SOCK_URL,
                json={"appid": token, "type": "GET_SENSORS"},
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            _LOGGER.debug(f"Erreur temps réel capteurs: {e}")
        
        return {}
    
    async def get_actions_realtime(self) -> dict:
        """Récupère l'état des actions en temps réel."""
        token = await self.get_token()
        if not token:
            return {}
        
        session = await self._get_session()
        
        try:
            async with session.post(
                self.SOCK_URL,
                json={"appid": token, "type": "GET_ACTIONS"},
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            _LOGGER.debug(f"Erreur temps réel actions: {e}")
        
        return {}
    
    def get_sensors(self) -> list:
        """Retourne la liste des capteurs."""
        return self._data.get("sensors", [])
    
    def get_devices(self) -> list:
        """Retourne la liste des appareils."""
        return self._data.get("devices", [])
    
    def get_actions(self) -> list:
        """Retourne la liste des actions."""
        return self._data.get("actions", [])
    
    def get_system_info(self) -> dict:
        """Retourne les informations système."""
        return self._data.get("system", {})
    
    async def start_websocket(self, callback=None):
        """Démarre la connexion WebSocket temps réel."""
        if self._websocket_connected:
            _LOGGER.debug("WebSocket déjà connecté")
            return True
        
        token = await self.get_token()
        if not token:
            _LOGGER.error("Impossible de démarrer WebSocket sans token")
            return False
        
        if callback:
            self._callbacks.append(callback)
        
        try:
            # Créer le client SocketIO
            self._sio = socketio.AsyncClient(
                logger=False,
                engineio_logger=False,
                reconnection=True,
                reconnection_attempts=0,  # Tentatives infinies
                reconnection_delay=5,
                reconnection_delay_max=30,
            )
            
            # Gestionnaires d'événements
            @self._sio.event
            async def connect():
                """Connexion établie."""
                _LOGGER.info("WebSocket Swimo connecté")
                self._websocket_connected = True
                
                # Authentification
                await self._sio.emit("authenticate", {"appid": token})
            
            @self._sio.event
            async def disconnect():
                """Déconnexion."""
                _LOGGER.warning("WebSocket Swimo déconnecté")
                self._websocket_connected = False
            
            @self._sio.event
            async def authentication(data):
                """Réponse d'authentification."""
                _LOGGER.info(f"WebSocket authentifié: {data}")
            
            @self._sio.event
            async def data(raw_data):
                """Données reçues - format complet toutes les 10 minutes."""
                try:
                    if isinstance(raw_data, str):
                        data = json.loads(raw_data)
                    else:
                        data = raw_data
                    
                    _LOGGER.debug(f"WebSocket data: {data.get('type')}")
                    
                    # Mise à jour des capteurs
                    if data.get("type") == "data" and "sensors" in data:
                        await self._update_sensors(data["sensors"])
                    
                    # Mise à jour des actions
                    if data.get("type") == "data" and "actions" in data:
                        await self._update_actions(data["actions"])
                    
                    # Notifier les callbacks
                    for cb in self._callbacks:
                        try:
                            await cb(data)
                        except Exception as e:
                            _LOGGER.error(f"Erreur callback: {e}")
                
                except Exception as e:
                    _LOGGER.error(f"Erreur traitement data WebSocket: {e}")
            
            @self._sio.event
            async def sensors_data(raw_data):
                """Mise à jour d'un capteur spécifique."""
                try:
                    if isinstance(raw_data, str):
                        data = json.loads(raw_data)
                    else:
                        data = raw_data
                    
                    _LOGGER.debug(f"WebSocket sensors-data: {data}")
                    
                    if "sensors" in data:
                        await self._update_sensors(data["sensors"])
                        
                        # Notifier les callbacks
                        for cb in self._callbacks:
                            try:
                                await cb(data)
                            except Exception as e:
                                _LOGGER.error(f"Erreur callback: {e}")
                
                except Exception as e:
                    _LOGGER.error(f"Erreur traitement sensors-data: {e}")
            
            @self._sio.event
            async def actions_status_data(raw_data):
                """Mise à jour du statut des actions."""
                try:
                    if isinstance(raw_data, str):
                        data = json.loads(raw_data)
                    else:
                        data = raw_data
                    
                    _LOGGER.debug(f"WebSocket actions-status-data: {data}")
                    
                    if "actions" in data:
                        await self._update_actions(data["actions"])
                        
                        # Notifier les callbacks
                        for cb in self._callbacks:
                            try:
                                await cb(data)
                            except Exception as e:
                                _LOGGER.error(f"Erreur callback: {e}")
                
                except Exception as e:
                    _LOGGER.error(f"Erreur traitement actions-status-data: {e}")
            
            # Connexion au WebSocket
            _LOGGER.info(f"Connexion au WebSocket: {self.WSS_URL}")
            await self._sio.connect(
                self.WSS_URL,
                transports=['websocket'],
                wait_timeout=10
            )
            
            return True
            
        except Exception as e:
            _LOGGER.error(f"Erreur démarrage WebSocket: {e}")
            self._websocket_connected = False
            return False
    
    async def _update_sensors(self, sensors_data):
        """Met à jour les données des capteurs depuis le WebSocket."""
        if "sensors" not in self._data:
            self._data["sensors"] = []
        
        for sensor_update in sensors_data:
            sensor_num = sensor_update.get("sensorNum")
            if not sensor_num:
                continue
            
            # Trouver et mettre à jour le capteur existant
            found = False
            for i, sensor in enumerate(self._data["sensors"]):
                if sensor.get("sensor_index") == sensor_num or sensor.get("sensorNum") == sensor_num:
                    # Mise à jour
                    if "value" in sensor_update:
                        self._data["sensors"][i]["sensor_value"] = sensor_update["value"]
                        self._data["sensors"][i]["value"] = sensor_update["value"]
                    if "valueRaw" in sensor_update:
                        self._data["sensors"][i]["valueRaw"] = sensor_update["valueRaw"]
                    found = True
                    break
            
            # Si non trouvé, l'ajouter
            if not found:
                self._data["sensors"].append({
                    "sensor_index": sensor_num,
                    "sensorNum": sensor_num,
                    "sensor_value": sensor_update.get("value"),
                    "value": sensor_update.get("value"),
                    "valueRaw": sensor_update.get("valueRaw", "")
                })
    
    async def _update_actions(self, actions_data):
        """Met à jour les données des actions depuis le WebSocket."""
        if "actions" not in self._data:
            self._data["actions"] = []
        
        for action_update in actions_data:
            action_num = action_update.get("actionNum")
            if not action_num:
                continue
            
            # Trouver et mettre à jour l'action existante
            found = False
            for i, action in enumerate(self._data["actions"]):
                if action.get("action_index") == action_num or action.get("actionNum") == action_num:
                    # Mise à jour
                    if "status" in action_update:
                        self._data["actions"][i]["status"] = action_update["status"]
                    if "mode" in action_update:
                        self._data["actions"][i]["mode"] = action_update["mode"]
                    if "sequence" in action_update:
                        self._data["actions"][i]["sequence"] = action_update["sequence"]
                    if "speed" in action_update:
                        self._data["actions"][i]["speed"] = action_update["speed"]
                    if "runtime" in action_update:
                        self._data["actions"][i]["runtime"] = action_update["runtime"]
                    found = True
                    break
            
            # Si non trouvé, l'ajouter
            if not found:
                self._data["actions"].append({
                    "action_index": action_num,
                    "actionNum": action_num,
                    "status": action_update.get("status", 0),
                    "mode": action_update.get("mode", 0),
                    "sequence": action_update.get("sequence", 0),
                    "speed": action_update.get("speed", 0),
                    "runtime": action_update.get("runtime", 0)
                })
    
    def is_websocket_connected(self) -> bool:
        """Vérifie si le WebSocket est connecté."""
        return self._websocket_connected
    
    def register_callback(self, callback):
        """Enregistre un callback pour les mises à jour WebSocket."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)