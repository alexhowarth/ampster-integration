"""
Ampster automation template: Control devices based on fetched JSON data.

This file demonstrates how to react to data updates from the coordinator and control Home Assistant devices.

NOTE: The example logic below is commented out by default. Uncomment and adapt it for your own use case.
If you leave it active and the referenced entity_id (e.g., 'switch.inverter') does not exist, Home Assistant will log a warning but the integration will still work.

This automation is triggered whenever new data is fetched (on the hour at the configured minute, or when manually refreshed).
"""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import logging

from .const import DOMAIN
# Import the cached timezone objects
from .coordinator import COUNTRY_TZ, DEFAULT_TZ

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER = logging.getLogger(__name__)

    async def handle_data_update():
        # NOTE: For robust automation, it's generally best to use UTC everywhere in your data and comparisons.
        # Localizing to country timezones (as below) is only needed if your data source is not UTC.
        # Consider standardizing all timestamps to UTC in your JSON and logic for simplicity and reliability.
        data = coordinator.data
        if data:
            timestamp = data.get("timestamp")
            country = data.get("country")
            current_period = data.get("current_period")
            _LOGGER.info(f"[Ampster] Data fetched. Timestamp: {timestamp}, Country: {country}, Current Period: {current_period}")

            import datetime
            # Use cached timezone objects to avoid blocking the event loop
            tz = COUNTRY_TZ.get(country, DEFAULT_TZ)

            now = datetime.datetime.now(tz)
            try:
                period_dt = datetime.datetime.fromisoformat(current_period)
                if period_dt.tzinfo is None:
                    period_dt = tz.localize(period_dt)
                if (period_dt.year == now.year and period_dt.month == now.month and
                    period_dt.day == now.day and period_dt.hour == now.hour):
                    _LOGGER.info(f"[Ampster] Data is current (current_period: {period_dt}, now: {now} in {tz})")
                else:
                    _LOGGER.info(f"[Ampster] Data is NOT current (current_period: {period_dt}, now: {now} in {tz})")
            except Exception as e:
                _LOGGER.debug(f"[Ampster] Could not parse or compare current_period: {e}")
        else:
            _LOGGER.info("[Ampster] Data fetched, but no data found!")

    # Log when fetching data, with URL and config
    _LOGGER.info(f"[Ampster] Fetching data from {coordinator.url} (country_prefix={coordinator.country_prefix}, minute={coordinator.minute})")

    def _listener():
        hass.async_create_task(handle_data_update())
    coordinator.async_add_listener(_listener)

    # Call once at startup to fetch/process data immediately
    await handle_data_update()
