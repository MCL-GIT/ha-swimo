# ============================================================================
# custom_components/swimo/sensor.py
# ============================================================================

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfTemperature
import logging

from .const import DOMAIN, SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configuration des capteurs."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    
    entities = []
    
    # Capteurs de mesure
    sensors = coordinator.data.get("sensors", [])
    for sensor in sensors:
        sensor_num = sensor.get("sensor_index") or sensor.get("sensorNum")
        if sensor_num:
            entities.append(SwimoSensor(coordinator, sensor, entry.entry_id))
    
    # Capteurs système
    system = coordinator.data.get("system", {})
    if isinstance(system, list) and len(system) > 0:
        system = system[0]
    
    if system:
        entities.append(SwimoSystemSensor(coordinator, "volume", "Volume", "m³", entry.entry_id))
        entities.append(SwimoSystemSensor(coordinator, "sys_type_display", "Type", "", entry.entry_id))
    
    async_add_entities(entities)


class SwimoSensor(CoordinatorEntity, SensorEntity):
    """Capteur de mesure Swimo (pH, température, etc.)."""
    
    def __init__(self, coordinator, sensor_data, entry_id):
        super().__init__(coordinator)
        self._sensor_data = sensor_data
        self._sensor_num = sensor_data.get("sensor_index") or sensor_data.get("sensorNum")
        self._entry_id = entry_id
        
        sensor_info = SENSOR_TYPES.get(self._sensor_num, {})
        self._attr_name = sensor_data.get("sensor_name") or sensor_info.get("name", f"Capteur {self._sensor_num}")
        self._attr_unique_id = f"swimo_{entry_id}_sensor_{self._sensor_num}"
        self._attr_icon = sensor_info.get("icon", "mdi:gauge")
        
        # Unité de mesure
        unit = sensor_data.get("sensor_unit") or sensor_info.get("unit")
        self._attr_native_unit_of_measurement = unit
        
        # Device class
        if self._sensor_num == 4:  # Température
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self):
        """Valeur du capteur."""
        sensors = self.coordinator.data.get("sensors", [])
        for sensor in sensors:
            sensor_num = sensor.get("sensor_index") or sensor.get("sensorNum")
            if sensor_num == self._sensor_num:
                value = sensor.get("sensor_value") or sensor.get("value")
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return value
        return None
    
    @property
    def extra_state_attributes(self):
        """Attributs supplémentaires."""
        sensors = self.coordinator.data.get("sensors", [])
        for sensor in sensors:
            sensor_num = sensor.get("sensor_index") or sensor.get("sensorNum")
            if sensor_num == self._sensor_num:
                attrs = {}
                if "valueRaw" in sensor:
                    attrs["raw_value"] = sensor["valueRaw"]
                if "sensor_type" in sensor:
                    attrs["type"] = sensor["sensor_type"]
                
                # Ajouter l'état de la connexion WebSocket
                api = self.hass.data[DOMAIN][self._entry_id]["api"]
                attrs["websocket_connected"] = api.is_websocket_connected()
                
                return attrs
        return {"websocket_connected": False}


class SwimoSystemSensor(CoordinatorEntity, SensorEntity):
    """Capteur d'information système."""
    
    def __init__(self, coordinator, key, name, unit, entry_id):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"Piscine {name}"
        self._attr_unique_id = f"swimo_{entry_id}_system_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = "mdi:information"
    
    @property
    def native_value(self):
        """Valeur du capteur système."""
        system = self.coordinator.data.get("system", {})
        if isinstance(system, list) and len(system) > 0:
            system = system[0]
        return system.get(self._key)

