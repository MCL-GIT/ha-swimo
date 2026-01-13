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

from .const import DOMAIN

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
    _LOGGER.info(f"Création de {len(sensors)} capteurs")
    
    for sensor in sensors:
        sensor_num = sensor.get("sensor_number")
        if sensor_num:
            entities.append(SwimoSensor(coordinator, sensor, entry.entry_id))
            _LOGGER.debug(f"Capteur créé: {sensor.get('sensor_name')} (#{sensor_num})")
    
    # Capteurs système
    system = coordinator.data.get("system", [])
    if system and len(system) > 0:
        entities.append(SwimoSystemSensor(coordinator, "sys_volume", "Volume piscine", "m³", entry.entry_id))
        entities.append(SwimoSystemSensor(coordinator, "sys_name", "Modèle", "", entry.entry_id))
    
    _LOGGER.info(f"Total entités créées: {len(entities)}")
    async_add_entities(entities)


class SwimoSensor(CoordinatorEntity, SensorEntity):
    """Capteur de mesure Swimo."""
    
    def __init__(self, coordinator, sensor_data, entry_id):
        super().__init__(coordinator)
        self._sensor_data = sensor_data
        self._sensor_num = sensor_data.get("sensor_number")
        self._entry_id = entry_id
        
        self._attr_name = f"Swimo {sensor_data.get('sensor_name', f'Capteur {self._sensor_num}')}"
        self._attr_unique_id = f"swimo_{entry_id}_sensor_{self._sensor_num}"
        
        # Icône selon le type de capteur
        sensor_hash = sensor_data.get("sensor_hash", "")
        if "PH" in sensor_hash:
            self._attr_icon = "mdi:ph"
        elif "TEMP" in sensor_hash:
            self._attr_icon = "mdi:thermometer"
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
        elif "ORP" in sensor_hash or "CL" in sensor_hash:
            self._attr_icon = "mdi:flask"
        elif "PRESSURE" in sensor_hash:
            self._attr_icon = "mdi:gauge"
        elif "TANK" in sensor_hash or "LEVEL" in sensor_hash:
            self._attr_icon = "mdi:water-percent"
        else:
            self._attr_icon = "mdi:gauge"
        
        # Unité de mesure
        self._attr_native_unit_of_measurement = sensor_data.get("sensor_unit")
        if self._attr_native_unit_of_measurement == "°C":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def native_value(self):
        """Valeur du capteur."""
        sensors = self.coordinator.data.get("sensors", [])
        for sensor in sensors:
            if sensor.get("sensor_number") == self._sensor_num:
                # Utiliser sensor_min qui contient la valeur actuelle
                value = sensor.get("sensor_min") or sensor.get("sensor_max")
                if value is not None and value != "":
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
            if sensor.get("sensor_number") == self._sensor_num:
                attrs = {
                    "sensor_status": sensor.get("sensor_status"),
                    "sensor_alarm": sensor.get("sensor_alarm") == "1",
                }
                
                if "sensor_raw_sensor" in sensor:
                    attrs["raw_value"] = sensor["sensor_raw_sensor"]
                
                if "sensor_text" in sensor:
                    attrs["status_text"] = sensor["sensor_text"].strip()
                
                # Limites
                if sensor.get("sensor_alarm_min"):
                    attrs["alarm_min"] = sensor["sensor_alarm_min"]
                if sensor.get("sensor_alarm_max"):
                    attrs["alarm_max"] = sensor["sensor_alarm_max"]
                
                # Connexion WebSocket
                api = self.hass.data[DOMAIN][self._entry_id]["api"]
                attrs["websocket_connected"] = api.is_websocket_connected()
                
                return attrs
        return {}


class SwimoSystemSensor(CoordinatorEntity, SensorEntity):
    """Capteur d'information système."""
    
    def __init__(self, coordinator, key, name, unit, entry_id):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"Swimo {name}"
        self._attr_unique_id = f"swimo_{entry_id}_system_{key}"
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = "mdi:information"
    
    @property
    def native_value(self):
        """Valeur du capteur système."""
        system = self.coordinator.data.get("system", [])
        if system and len(system) > 0:
            return system[0].get(self._key)
        return None