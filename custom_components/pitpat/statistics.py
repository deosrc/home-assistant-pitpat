"""Import PitPat daily activity into Home Assistant long-term statistics.

This is mostly for the Bluetooth Activity Tracker, but can also be used for the GPS
Tracker.

For the Bluetooth Tracker, the device stores up to 10 days of activity and only
uploads the data when synced via the PitPat app. The entities only show the latest
information from the API, meaning that:

- Historic data would not be available unless synced every day.
- The stats for a given day would only cover up to the point where the data is synced.

This module is called from the coordinator update method to solve this problem by
writing historic data to statistics. This will re-import the whole window on every
refresh and therefore repair history retroactively, whenever the user happens to sync.

Note that Home Assistant will automatically record statistics for entities and use these
for various graphs. These are likely more useful for the GPS tracker (unless it loses
signal). Updating the entity statistics retro-actively may cause unexpected results and
is not recommended. Therefore, the statistics here are imported to separate "external"
statistics visible at `/config/tools/statistics` or via the `recorder.get_statistics`
action. The Ids are `pitpat:<dog_name>_<stat>_daily`. Dog name was used in rather than
dog Id as the search in the select field for `recorder.get_statistics` seems to only
search on the Statistic Id. Therefore, using the dog name makes them more easily
accessible.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging

from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.components.recorder.statistics import async_add_external_statistics
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

try:  # HA >= 2025.8 -- has_mean is deprecated and removed in 2026.11
    from homeassistant.components.recorder.models import StatisticMeanType

    _MEAN_META = {"mean_type": StatisticMeanType.ARITHMETIC}
except ImportError:  # pragma: no cover - older cores
    _MEAN_META = {"has_mean": True}

try:  # unit_class must name a real converter, or be None
    from homeassistant.util.unit_conversion import DistanceConverter

    _DISTANCE_CLASS = DistanceConverter.UNIT_CLASS
except (ImportError, AttributeError):  # pragma: no cover
    _DISTANCE_CLASS = None

try:  # unit_class must name a real converter, or be None
    from homeassistant.util.unit_conversion import DurationConverter

    _DURATION_CLASS = DurationConverter.UNIT_CLASS
except (ImportError, AttributeError):  # pragma: no cover
    _DURATION_CLASS = None

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# The device only holds 10 days, but re-importing a wider window is harmless and
# covers the case where the API returns more than the device buffered.
MAX_DAYS = 30


@dataclass(frozen=True, kw_only=True)
class PitPatStatisticsDescription():
    statistic_key: str
    data_key: str
    label: str
    unit_of_measurement: str
    unit_class: str | None = None
    value_scale: float = 1


# unit_class is None where no unit converter applies; steps/kcal/minutes are all
# left unconverted rather than guessing at a converter that may reject the unit.
METRICS = [
    PitPatStatisticsDescription(
        statistic_key = "steps",
        data_key = "TotalSteps",
        label = "Steps",
        unit_of_measurement = "steps",
    ),
    PitPatStatisticsDescription(
        statistic_key = "distance",
        data_key = "TotalDistance",
        label = "Distance",
        unit_of_measurement = "km",
        unit_class = _DISTANCE_CLASS,
        value_scale = 0.001,
    ),
    PitPatStatisticsDescription(
        statistic_key = "calories",
        data_key = "TotalCalories",
        label = "Calories",
        unit_of_measurement = "kcal",
    ),
    PitPatStatisticsDescription(
        statistic_key = "walking",
        data_key = "TotalWalkMinutes",
        label = "Walking",
        unit_of_measurement = "min",
        unit_class = _DURATION_CLASS,
    ),
    PitPatStatisticsDescription(
        statistic_key = "running",
        data_key = "TotalRunMinutes",
        label = "Running",
        unit_of_measurement = "min",
        unit_class = _DURATION_CLASS,
    ),
    PitPatStatisticsDescription(
        statistic_key = "playing",
        data_key = "TotalPlayMinutes",
        label = "Playing",
        unit_of_measurement = "min",
        unit_class = _DURATION_CLASS,
    ),
    PitPatStatisticsDescription(
        statistic_key = "pottering",
        data_key = "TotalPotteringMinutes",
        label = "Pottering",
        unit_of_measurement = "min",
        unit_class = _DURATION_CLASS,
    ),
    PitPatStatisticsDescription(
        statistic_key = "resting",
        data_key = "TotalRestMinutes",
        label = "Resting",
        unit_of_measurement = "min",
        unit_class = _DURATION_CLASS,
    ),
    PitPatStatisticsDescription(
        statistic_key = "exercising",
        data_key = "Activeness",
        label = "Exercising",
        unit_of_measurement = "min",
        unit_class = _DURATION_CLASS,
    ),
]


def _slug(value: str) -> str:
    """Reduce a name to something safe for a statistic_id."""
    out = "".join(c.lower() if c.isalnum() else "_" for c in value)
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_") or "dog"


def _day_start(raw_date) -> datetime | None:
    """Return the UTC instant of local midnight for an API date.

    Statistics must start on an hour boundary. Local midnight converted to UTC
    satisfies that for whole-hour timezones, which covers UK/EU usage.
    """
    if not raw_date:
        return None

    parsed = None
    if isinstance(raw_date, datetime):
        parsed = raw_date
    elif isinstance(raw_date, str):
        parsed = dt_util.parse_datetime(raw_date)
        if parsed is None:
            parsed = dt_util.parse_date(raw_date)

    if parsed is None:
        return None

    if isinstance(parsed, datetime):
        day = (dt_util.as_local(parsed) if parsed.tzinfo else parsed).date()
    else:
        day = parsed

    local_midnight = datetime.combine(
        day, datetime.min.time(), tzinfo=dt_util.DEFAULT_TIME_ZONE
    )
    return dt_util.as_utc(local_midnight)


def async_import_activity_history(
    hass: HomeAssistant, dog_name: str | None, all_activity_days: list | None
) -> None:
    """Write each day's totals into long-term statistics.

    Re-importing an existing day overwrites it, which is what makes a late sync
    correct the record rather than duplicate it.
    """
    if not all_activity_days:
        return

    days = sorted(all_activity_days, key=lambda d: d.get("Date") or "")[-MAX_DAYS:]
    dog = _slug(dog_name or "dog")
    imported = 0

    for description in METRICS:
        points: list[StatisticData] = []

        for day in days:
            start = _day_start(day.get("Date"))
            value = day.get(description.data_key)
            if start is None or value is None:
                continue
            try:
                scaled = float(value) * description.value_scale
            except (TypeError, ValueError):
                continue
            # One point per day: mean/min/max are equal so any rollup period
            # renders the day's total.
            points.append(
                StatisticData(start=start, mean=scaled, min=scaled, max=scaled)
            )

        if not points:
            continue

        metadata = StatisticMetaData(
            **_MEAN_META,
            has_sum=False,
            name=f"{dog_name or 'Dog'} {description.label} (daily)",
            source=DOMAIN,
            statistic_id=f"{DOMAIN}:{dog}_{description.statistic_key}_daily",
            unit_of_measurement=description.unit_of_measurement,
            unit_class=description.unit_class,
        )
        async_add_external_statistics(hass, metadata, points)
        imported += 1

    _LOGGER.debug(
        "Imported daily statistics for %s: %s metrics across %s days",
        dog_name,
        imported,
        len(days),
    )
