
from datetime import datetime, timedelta
import logging
from typing import Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator
)
from homeassistant.util import dt as dt_util

from .api import InvalidCredentialsError, PitPatApiClient
from .const import DOMAIN
from .statistics import async_import_activity_history

_LOGGER = logging.getLogger(__name__)

TCoordinatorData = Dict[str, dict]


def _day_is_today(date_value: str | None, reference: datetime | None = None) -> bool:
    """Return whether an activity date falls on the same day as the reference.

    Without a reference, the current local time is used. A date-only value is
    compared directly, while a datetime is converted to local time first.
    """
    if not date_value:
        return False

    parsed = dt_util.parse_datetime(date_value)
    if parsed is None:
        parsed = dt_util.parse_date(date_value)
    if parsed is None:
        return False

    if isinstance(parsed, datetime):
        day = (dt_util.as_local(parsed) if parsed.tzinfo else parsed).date()
    else:
        day = parsed

    if reference is None:
        return day == dt_util.now().date()
    ref_local = dt_util.as_local(reference) if getattr(reference, 'tzinfo', None) else reference
    return day == ref_local.date()


def _get_activity_today(all_activity_days: list | None, reference: datetime | None = None) -> dict | None:
    """Return the most recent activity day, but only if it is for today.

    The tracker may not have been seen today (e.g. no signal or battery), in
    which case the most recent activity is stale and should not be shown as
    today's stats.
    """
    if not all_activity_days:
        return None

    most_recent = sorted(
        all_activity_days, key=lambda item: item.get('Date') or '', reverse=True
    )[0]

    if not _day_is_today(most_recent.get('Date'), reference):
        return None

    return most_recent

def _is_tracking_active(data: TCoordinatorData | None) -> bool:
    """Return whether live tracking is active for any dog."""
    return any(
        ((dog.get('monitor_details') or {}).get('LiveTrackingReason') or 0) != 0
        for dog in (data or {}).values()
    )


class PitPatDataUpdateCoordinator(DataUpdateCoordinator[TCoordinatorData]):
    """DataUpdateCoordinator to handle fetching data from PitPat."""

    def __init__(self, hass: HomeAssistant, update_interval: int, tracking_update_interval: int, config_entry: ConfigEntry):
        """Initialize the coordinator and set up the Controller object."""
        self._hass = hass

        self._available = True
        self._normal_interval = timedelta(minutes=update_interval)
        self._tracking_interval = timedelta(seconds=tracking_update_interval)
        self.api_client: PitPatApiClient | None = None

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=self._normal_interval,
        )

    def set_intervals(self, update_interval: int, tracking_update_interval: int) -> None:
        """Update the configured intervals (minutes, seconds) and apply the right one."""
        self._normal_interval = timedelta(minutes=update_interval)
        self._tracking_interval = timedelta(seconds=tracking_update_interval)
        self._apply_interval(self.data)

    def _apply_interval(self, data: TCoordinatorData | None) -> None:
        """Pick the poll interval for the given data, logging when it changes."""
        tracking = _is_tracking_active(data)
        new_interval = self._tracking_interval if tracking else self._normal_interval
        if new_interval != self.update_interval:
            _LOGGER.info(
                'Tracking %s: poll interval changed from %s to %s',
                'active' if tracking else 'inactive',
                self.update_interval,
                new_interval,
            )
        self.update_interval = new_interval
        _LOGGER.debug('Next poll in %s', new_interval)

    async def _async_ensure_ready(self):
        if not self.api_client:
            await self._async_refresh_auth()

        is_authenticated = await self.api_client.async_ensure_user_id_present()
        if not is_authenticated:
            raise ConfigEntryAuthFailed()

    async def _async_refresh_auth(self):
        _LOGGER.info('Preparing new API client from refresh token.')
        try:
            session = async_create_clientsession(self._hass)
            tokens = await PitPatApiClient.async_authenticate_from_refresh_token(session, self.config_entry.data.get('refresh_token'))
            self.api_client = PitPatApiClient(session, tokens)
        except InvalidCredentialsError as err:
            raise ConfigEntryAuthFailed() from err

    async def _async_update_data(self) -> TCoordinatorData:
        """Fetch data"""
        data = await self._async_fetch_with_retry()
        # Poll faster while tracking is active. The next refresh is scheduled
        # after this returns, so it picks up the new interval.
        self._apply_interval(data)
        return data

    async def _async_fetch_with_retry(self) -> TCoordinatorData:
        try:
            return await self._async_refresh_data()
        except ConfigEntryAuthFailed as err:
            _LOGGER.info('API client is not authenticated. Attempting to re-authenticate.', exc_info=err)
            self.api_client = None
            return await self._async_refresh_data()
        except Exception as err:
            _LOGGER.warning('Request failed. Retrying with new API client.', exc_info=err)
            self.api_client = None
            return await self._async_refresh_data()

    async def _async_refresh_data(self) -> TCoordinatorData:
        await self._async_ensure_ready()

        dogs = await self.api_client.async_get_dogs()
        data = { d['Id']: d for d in dogs}

        for dog_id in data.keys():
            data[dog_id] = {
                **data[dog_id],
                **await self._async_update_dog_data(dog_id, data[dog_id].get('Name'))
            }

        return data

    async def _async_update_dog_data(self, dog_id, dog_name=None) -> dict:
        monitor_details = await self.api_client.async_get_monitor(dog_id)
        all_activity_days = await self.api_client.async_get_all_activity_days(dog_id)

        # The live sensors only ever expose today's record, so a day completed
        # by a later sync is fetched and discarded. Push every buffered day into
        # long-term statistics instead, which corrects history retroactively.
        try:
            async_import_activity_history(self._hass, dog_name, all_activity_days)
        except Exception:  # statistics must never break the data refresh
            _LOGGER.exception('Failed to import daily activity statistics')

        return {
            'monitor_details': monitor_details,
            'activity_today': _get_activity_today(all_activity_days),
        }
