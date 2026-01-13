# ============================================================================
# number.py - Contrôles numériques
# ============================================================================
"""Contrôles numériques Swimo."""
from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import logging

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configuration des entités numériques."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    
    entities = []
    
    # Chercher les actions avec setpoint (chauffage, pompes doseuses)
    actions = coordinator.data.get("actions", [])
    for action in actions:
        if action.get("device_setpoint") and action.get("device_min_setpoint"):
            entities.append(SwimoSetpoint(coordinator, api, action, entry.entry_id))
            _LOGGER.debug(f"Number créé: {action.get('device_name')} setpoint")
    
    async_add_entities(entities)


class SwimoSetpoint(CoordinatorEntity, NumberEntity):
    """Entité pour régler une consigne."""
    
    def __init__(self, coordinator, api, device_data, entry_id):
        super().__init__(coordinator)
        self._api = api
        self._device_data = device_data
        self._device_num = device_data.get("device_number")
        
        device_name = device_data.get("device_name", f"Device {self._device_num}")
        self._attr_name = f"Swimo {device_name} Consigne"
        self._attr_unique_id = f"swimo_{entry_id}_setpoint_{self._device_num}"
        self._attr_icon = "mdi:target"
        
        # Limites et unité
        try:
            self._attr_native_min_value = float(device_data.get("device_min_setpoint", 0))
            self._attr_native_max_value = float(device_data.get("device_max_setpoint", 100))
        except:
            self._attr_native_min_value = 0
            self._attr_native_max_value = 100
        
        self._attr_native_step = 0.5
        self._attr_native_unit_of_measurement = device_data.get("device_unit_setpoint", "")
    
    @property
    def native_value(self):
        """Valeur actuelle."""
        actions = self.coordinator.data.get("actions", [])
        for action in actions:
            if action.get("device_number") == self._device_num:
                setpoint = action.get("device_setpoint")
                if setpoint:
                    try:
                        return float(setpoint)
                    except:
                        pass
        return None
    
    async def async_set_native_value(self, value: float) -> None:
        """Définir la consigne."""
        success = await self._api.update_device(
            key="device_setpoint",
            value=str(value),
            number=int(self._device_num)
        )
        if success:
            await self.coordinator.async_request_refresh()
