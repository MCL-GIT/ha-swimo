# ============================================================================
# binary_sensor.py - Capteurs binaires
# ============================================================================
"""Capteurs binaires Swimo."""
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
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
    """Configuration des capteurs binaires."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    
    entities = []
    
    # Capteur de connexion WebSocket
    entities.append(SwimoWebSocketSensor(coordinator, api, entry.entry_id))
    
    # Alarmes
    alarms = coordinator.data.get("alarms", [])
    for alarm in alarms:
        alarm_num = alarm.get("alarm_index") or alarm.get("alarm_number")
        if alarm_num:
            entities.append(SwimoAlarm(coordinator, alarm, entry.entry_id))
    
    # Capteurs d'alarme dans les sensors
    sensors = coordinator.data.get("sensors", [])
    for sensor in sensors:
        if sensor.get("sensor_alarm") == "1":
            entities.append(SwimoSensorAlarm(coordinator, sensor, entry.entry_id))
    
    async_add_entities(entities)


class SwimoWebSocketSensor(CoordinatorEntity, BinarySensorEntity):
    """Capteur d'état de la connexion WebSocket."""
    
    def __init__(self, coordinator, api, entry_id):
        super().__init__(coordinator)
        self._api = api
        self._attr_name = "Swimo Connexion Temps Réel"
        self._attr_unique_id = f"swimo_{entry_id}_websocket"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_icon = "mdi:wifi"
    
    @property
    def is_on(self):
        """État de la connexion WebSocket."""
        return self._api.is_websocket_connected()
    
    @property
    def extra_state_attributes(self):
        """Attributs supplémentaires."""
        return {
            "mode": "WebSocket temps réel" if self.is_on else "Polling HTTP",
            "url": "wss://now.swimo.io" if self.is_on else "https://socket.swimo.io"
        }


class SwimoAlarm(CoordinatorEntity, BinarySensorEntity):
    """Capteur d'alarme."""
    
    def __init__(self, coordinator, alarm_data, entry_id):
        super().__init__(coordinator)
        self._alarm_data = alarm_data
        self._alarm_num = alarm_data.get("alarm_index") or alarm_data.get("alarm_number")
        
        self._attr_name = f"Swimo {alarm_data.get('alarm_name', f'Alarme {self._alarm_num}')}"
        self._attr_unique_id = f"swimo_{entry_id}_alarm_{self._alarm_num}"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
    
    @property
    def is_on(self):
        """État de l'alarme."""
        alarms = self.coordinator.data.get("alarms", [])
        for alarm in alarms:
            alarm_num = alarm.get("alarm_index") or alarm.get("alarm_number")
            if alarm_num == self._alarm_num:
                return alarm.get("alarm_status", 0) == 1
        return False


class SwimoSensorAlarm(CoordinatorEntity, BinarySensorEntity):
    """Alarme associée à un capteur."""
    
    def __init__(self, coordinator, sensor_data, entry_id):
        super().__init__(coordinator)
        self._sensor_num = sensor_data.get("sensor_number")
        
        self._attr_name = f"Swimo {sensor_data.get('sensor_name')} Alarme"
        self._attr_unique_id = f"swimo_{entry_id}_sensor_alarm_{self._sensor_num}"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
    
    @property
    def is_on(self):
        """État de l'alarme."""
        sensors = self.coordinator.data.get("sensors", [])
        for sensor in sensors:
            if sensor.get("sensor_number") == self._sensor_num:
                return sensor.get("sensor_alarm") == "1"
        return False