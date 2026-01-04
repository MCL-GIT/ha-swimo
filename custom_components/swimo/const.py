"""Constantes pour l'intégration Swimo."""

DOMAIN = "swimo"

SENSOR_TYPES = {
    1: {"name": "pH", "unit": "pH", "icon": "mdi:ph"},
    2: {"name": "Redox", "unit": "mV", "icon": "mdi:water-check"},
    3: {"name": "Chlore", "unit": "mg/L", "icon": "mdi:flask"},
    4: {"name": "Température", "unit": "°C", "icon": "mdi:thermometer"},
    5: {"name": "Pression", "unit": "bar", "icon": "mdi:gauge"},
    7: {"name": "Débit", "unit": "m³/h", "icon": "mdi:water-pump"},
    8: {"name": "Conductivité", "unit": "g/L", "icon": "mdi:sine-wave"},
    12: {"name": "Niveau d'eau", "unit": "", "icon": "mdi:waves"},
}

DEVICE_TYPES = {
    "pump": {"name": "Pompe", "icon": "mdi:pump"},
    "light": {"name": "Éclairage", "icon": "mdi:lightbulb"},
    "heater": {"name": "Chauffage", "icon": "mdi:radiator"},
    "filter": {"name": "Filtration", "icon": "mdi:air-filter"},
    "ph_pump": {"name": "Pompe pH", "icon": "mdi:water-plus"},
    "chlorine_pump": {"name": "Pompe Chlore", "icon": "mdi:flask"},
}

WEBSOCKET_ENABLED = True
WEBSOCKET_RECONNECT_DELAY = 5
