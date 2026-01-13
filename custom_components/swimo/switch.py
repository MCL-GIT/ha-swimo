# ============================================================================
# custom_components/swimo/switch.py
# ============================================================================

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import logging

from .const import DOMAIN, DEVICE_TYPES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configuration des switches."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    api = hass.data[DOMAIN][entry.entry_id]["api"]
    
    entities = []
    
    # Appareils contrôlables
    devices = coordinator.data.get("devices", [])
    for device in devices:
        device_num = device.get("device_index")
        if device_num:
            entities.append(SwimoSwitch(coordinator, api, device, entry.entry_id))
    
    # Actions contrôlables
    actions = coordinator.data.get("actions", [])
    for action in actions:
        action_num = action.get("action_index") or action.get("actionNum")
        if action_num:
            entities.append(SwimoActionSwitch(coordinator, api, action, entry.entry_id))
    
    async_add_entities(entities)


class SwimoSwitch(CoordinatorEntity, SwitchEntity):
    """Switch pour contrôler les équipements."""
    
    def __init__(self, coordinator, api, device_data, entry_id):
        super().__init__(coordinator)
        self._api = api
        self._device_data = device_data
        self._device_num = device_data.get("device_index")
        self._entry_id = entry_id
        
        self._attr_name = device_data.get("device_name", f"Appareil {self._device_num}")
        self._attr_unique_id = f"swimo_{entry_id}_device_{self._device_num}"
        
        device_type = device_data.get("device_type", "").lower()
        device_info = DEVICE_TYPES.get(device_type, {})
        self._attr_icon = device_info.get("icon", "mdi:power")
    
    @property
    def is_on(self):
        """État du switch."""
        devices = self.coordinator.data.get("devices", [])
        for device in devices:
            if device.get("device_index") == self._device_num:
                mode = device.get("device_mode", 0)
                status = device.get("device_status", 0)
                return mode == 1 or status == 1
        return False
    
    async def async_turn_on(self, **kwargs):
        """Allumer l'équipement."""
        success = await self._api.update_device(
            key="device_mode",
            value="1",
            number=self._device_num
        )
        if success:
            await self.coordinator.async_request_refresh()
    
    async def async_turn_off(self, **kwargs):
        """Éteindre l'équipement."""
        success = await self._api.update_device(
            key="device_mode",
            value="0",
            number=self._device_num
        )
        if success:
            await self.coordinator.async_request_refresh()


class SwimoActionSwitch(CoordinatorEntity, SwitchEntity):
    """Switch pour contrôler les actions."""
    
    def __init__(self, coordinator, api, action_data, entry_id):
        super().__init__(coordinator)
        self._api = api
        self._action_data = action_data
        self._action_num = action_data.get("action_index") or action_data.get("actionNum")
        self._entry_id = entry_id
        
        self._attr_name = action_data.get("action_name", f"Action {self._action_num}")
        self._attr_unique_id = f"swimo_{entry_id}_action_{self._action_num}"
        self._attr_icon = "mdi:play-circle"
    
    @property
    def is_on(self):
        """État de l'action."""
        actions = self.coordinator.data.get("actions", [])
        for action in actions:
            action_num = action.get("action_index") or action.get("actionNum")
            if action_num == self._action_num:
                status = action.get("status", 0)
                mode = action.get("mode", 0)
                return status == 1 or mode == 1
        return False
    
    async def async_turn_on(self, **kwargs):
        """Activer l'action."""
        success = await self._api.update_device(
            key="action_mode",
            value="1",
            number=self._action_num
        )
        if success:
            await self.coordinator.async_request_refresh()
    
    async def async_turn_off(self, **kwargs):
        """Désactiver l'action."""
        success = await self._api.update_device(
            key="action_mode",
            value="0",
            number=self._action_num
        )
        if success:
            await self.coordinator.async_request_refresh()

