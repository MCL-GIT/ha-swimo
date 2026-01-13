# ============================================================================
# config_flow.py - Flux de configuration
# ============================================================================
"""Flux de configuration Swimo."""
from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol
from .const import DOMAIN
from .api import SwimoAPI
import logging

_LOGGER = logging.getLogger(__name__)

class SwimoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestion du flux de configuration."""
    
    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        """Gestion de l'étape utilisateur."""
        errors = {}
        
        if user_input is not None:
            # Vérification des identifiants
            api = SwimoAPI(user_input["email"], user_input["password"])
            
            try:
                token = await api.get_token()
                
                if token:
                    await self.async_set_unique_id(user_input["email"].lower())
                    self._abort_if_unique_id_configured()
                    
                    # Récupérer les infos système pour le titre
                    data = await api.get_all_data()
                    system_name = "Piscine"
                    
                    if data and "system" in data:
                        sys_info = data["system"]
                        if isinstance(sys_info, list) and len(sys_info) > 0:
                            sys_info = sys_info[0]
                            system_name = sys_info.get("sys_name", "Piscine").capitalize()
                    
                    await api.close()
                    
                    return self.async_create_entry(
                        title=f"Swimo - {system_name}",
                        data=user_input
                    )
                else:
                    errors["base"] = "auth_error"
            except Exception as e:
                _LOGGER.error(f"Erreur configuration: {e}")
                errors["base"] = "unknown"
            finally:
                await api.close()
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("email"): str,
                vol.Required("password"): str,
            }),
            errors=errors,
            description_placeholders={
                "email": "Votre email Swimo",
                "password": "Votre mot de passe"
            }
        )