"""
Intégration Swimo/Orkestron pour Home Assistant
Version améliorée avec support WebSocket temps réel
"""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from datetime import timedelta
import logging
import asyncio

from .api import SwimoAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.SWITCH, Platform.NUMBER, Platform.BINARY_SENSOR]
SCAN_INTERVAL = timedelta(seconds=30)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configuration de l'intégration Swimo."""
    hass.data.setdefault(DOMAIN, {})
    
    api = SwimoAPI(entry.data["email"], entry.data["password"])
    
    # Créer le coordinateur de données
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=api.get_all_data,
        update_interval=SCAN_INTERVAL,
    )
    
    # Première mise à jour
    await coordinator.async_config_entry_first_refresh()
    
    # Callback pour les mises à jour WebSocket
    async def websocket_callback(data):
        """Callback appelé lors de mises à jour WebSocket."""
        _LOGGER.debug(f"WebSocket callback: {data.get('type')}")
        # Demander une mise à jour du coordinateur
        await coordinator.async_request_refresh()
    
    # Démarrer le WebSocket en arrière-plan
    async def start_websocket():
        """Démarre la connexion WebSocket."""
        try:
            # Attendre un peu pour que l'intégration soit prête
            await asyncio.sleep(5)
            success = await api.start_websocket(callback=websocket_callback)
            if success:
                _LOGGER.info("WebSocket Swimo démarré avec succès")
            else:
                _LOGGER.warning("Échec démarrage WebSocket, utilisation du polling uniquement")
        except Exception as e:
            _LOGGER.error(f"Erreur démarrage WebSocket: {e}")
    
    # Lancer le WebSocket de manière asynchrone
    hass.async_create_task(start_websocket())
    
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Déchargement de l'intégration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        api = hass.data[DOMAIN][entry.entry_id]["api"]
        await api.close()
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
