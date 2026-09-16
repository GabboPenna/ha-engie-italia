"""A single manual refresh shared by all supplies in the account."""

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([EngieRefreshButton(entry.runtime_data, entry)])


class EngieRefreshButton(CoordinatorEntity, ButtonEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "refresh"
    _attr_device_class = ButtonDeviceClass.UPDATE

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.unique_id}_refresh"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            name="ENGIE Italia",
            manufacturer="ENGIE",
            model="Account",
        )

    async def async_press(self):
        await self.coordinator.async_request_refresh()
