# ============================================================================
# custom_components/swimo/number.py
# ============================================================================

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
    
    # Consignes de température
    sensors = coordinator.data.get("sensors", [])
    for sensor in sensors:
        sensor_num = sensor.get("sensor_index") or sensor.get("sensorNum")
        if sensor_num == 4:  # Capteur de température
            # Ajouter consigne température
            entities.append(SwimoTempSetpoint(coordinator, api, entry.entry_id))
    
    async_add_entities(entities)


class SwimoTempSetpoint(CoordinatorEntity, NumberEntity):
    """Entité pour régler la température cible."""
    
    def __init__(self, coordinator, api, entry_id):
        super().__init__(coordinator)
        self._api = api
        self._attr_name = "Température Cible"
        self._attr_unique_id = f"swimo_{entry_id}_temp_setpoint"
        self._attr_icon = "mdi:thermometer-lines"
        self._attr_native_min_value = 15
        self._attr_native_max_value = 35
        self._attr_native_step = 0.5
        self._attr_native_unit_of_measurement = "°C"
    
    @property
    def native_value(self):
        """Valeur actuelle."""
        system = self.coordinator.data.get("system", {})
        if isinstance(system, list) and len(system) > 0:
            system = system[0]
        return system.get("sys_temp_target", 27)
    
    async def async_set_native_value(self, value: float) -> None:
        """Définir la température cible."""
        success = await self._api.update_device(
            key="sys_temp_target",
            value=str(value)
        )
        if success:
            await self.coordinator.async_request_refresh()
