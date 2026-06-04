"""
Map TNS photometry (instrument + filter names) to YSE telescope / instrument / band.

TNS API returns separate fields, e.g. instrument=ZTF-Cam, filter=r.
The TNS web UI often shows composite labels: P48_ZTF-Cam_r, ATLAS-TDO_ATLAS-05_wide.

YSE stores short PhotometricBand.name tokens (e.g. r, g, w) scoped by Instrument.
Light-curve code uses str(band) -> "Band: {instrument} - {name}" for bandpassdict lookups.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

# TNS instrument name -> YSE telescope + instrument (+ optional obs_group hint)
TNS_INSTRUMENT_MAP: Dict[str, Dict[str, str]] = {
    "ZTF-Cam": {"telescope": "P48", "instrument": "ZTF-Cam", "obs_group": "ZTF"},
    "GPC1": {"telescope": "Pan-STARRS1", "instrument": "GPC1", "obs_group": "Pan-STARRS1"},
    "GPC2": {"telescope": "Pan-STARRS2", "instrument": "GPC2", "obs_group": "Pan-STARRS2"},
    "ATLAS-05": {"telescope": "ATLAS-TDO", "instrument": "ATLAS-05", "obs_group": "ATLAS"},
    "ATLAS-01": {"telescope": "ATLAS-TDO", "instrument": "ATLAS-01", "obs_group": "ATLAS"},
    "ATLAS-02": {"telescope": "ATLAS-TDO", "instrument": "ATLAS-02", "obs_group": "ATLAS"},
    "ATLAS-03": {"telescope": "ATLAS-TDO", "instrument": "ATLAS-03", "obs_group": "ATLAS"},
    "ATLAS-04": {"telescope": "ATLAS-TDO", "instrument": "ATLAS-04", "obs_group": "ATLAS"},
    "ATLAS-06": {"telescope": "ATLAS-TDO", "instrument": "ATLAS-06", "obs_group": "ATLAS"},
    "ATLAS-07": {"telescope": "ATLAS-TDO", "instrument": "ATLAS-07", "obs_group": "ATLAS"},
    "ATLAS-08": {"telescope": "ATLAS-TDO", "instrument": "ATLAS-08", "obs_group": "ATLAS"},
    "WFST-WFC": {"telescope": "WFST", "instrument": "WFC", "obs_group": "WFST"},
    "GOTO-1": {"telescope": "GOTO-N", "instrument": "GOTO-1", "obs_group": "GOTO"},
    "GOTO-2": {"telescope": "GOTO-N", "instrument": "GOTO-2", "obs_group": "GOTO"},
    "BlackGEM-Cam3": {"telescope": "BG3", "instrument": "BG-Cam3", "obs_group": "BlackGEM"},
    "BlackGEM-Cam2": {"telescope": "BG2", "instrument": "BG-Cam2", "obs_group": "BlackGEM"},
    "CFH12k": {"telescope": "CFHT", "instrument": "CFH12k", "obs_group": "PTF"},
    # Legacy ATLAS path in YSE DB (HKO ACAM1)
    "ACAM1": {"telescope": "ATLAS - HKO", "instrument": "ACAM1", "obs_group": "ATLAS"},
}

# TNS filter token (any casing) -> short YSE PhotometricBand.name
FILTER_ALIASES: Dict[str, str] = {
    "bg-q-blackgem": "q",
    "bg-q": "q",
    "g-p1": "g",
    "r-p1": "r",
    "i-p1": "i",
    "z-p1": "z",
    "y-p1": "y",
    "g-ztf": "g",
    "r-ztf": "r",
    "i-ztf": "i",
    "z-ztf": "z",
    "r-wfst": "r",
    "g-wfst": "g",
    "l-goto": "L",
    "g-goto": "g",
    "wide-atlas": "w",
    "orange-atlas": "o",
    "cyan-atlas": "c",
    "wide": "w",
    "orange": "o",
    "cyan": "c",
}

_SURVEY_SUFFIXES = (
    "-ztf",
    "-atlas",
    "-wfst",
    "-goto",
    "-ptf",
    "-p1",
    "-blackgem",
    "-blackgem",
    "-sloan",
)


@dataclass(frozen=True)
class ResolvedTnsPhotometry:
    telescope: str
    instrument: str
    band: str
    obs_group_hint: Optional[str] = None
    tns_instrument: str = ""
    tns_filter: str = ""


def parse_tns_composite_label(label: str) -> Optional[ResolvedTnsPhotometry]:
    """
    Parse TNS-style composite names: {telescope}_{instrument}_{filter}.

    Examples:
        P48_ZTF-Cam_r -> P48 / ZTF-Cam / r
        ATLAS-TDO_ATLAS-05_wide -> ATLAS-TDO / ATLAS-05 / w
        BG3_BlackGEM-Cam3_BG-q -> BG3 / BG-Cam3 / q
    """
    if not label or "_" not in label:
        return None
    parts = label.strip().split("_")
    if len(parts) < 3:
        return None
    tns_filter = parts[-1]
    telescope = parts[0]
    tns_instrument = "_".join(parts[1:-1])
    return resolve_tns_photometry(tns_instrument, tns_filter, telescope_hint=telescope)


def normalize_band_name(tns_instrument: str, band_token: str) -> str:
    """Map TNS filter token to short YSE PhotometricBand.name (instrument carries survey)."""
    token = (band_token or "Unknown").strip()
    if not token:
        return "Unknown"
    key = token.lower()
    if key in FILTER_ALIASES:
        return FILTER_ALIASES[key]
    for suffix in _SURVEY_SUFFIXES:
        if key.endswith(suffix):
            key = key[: -len(suffix)]
            break
    if key in FILTER_ALIASES:
        return FILTER_ALIASES[key]
    if key in ("wide", "orange", "cyan"):
        return {"wide": "w", "orange": "o", "cyan": "c"}[key]
    if len(key) == 1:
        return token if token.isupper() and len(token) == 1 else key
    if key in ("g", "r", "i", "z", "y", "u", "w", "o", "c", "q"):
        return key
    if key == "l":
        return "L"
    return token


def resolve_tns_photometry(
    tns_instrument: str,
    tns_filter: str,
    *,
    telescope_hint: Optional[str] = None,
) -> ResolvedTnsPhotometry:
    """
    Resolve TNS instrument + filter to YSE telescope, instrument, and band names.
    """
    raw_inst = (tns_instrument or "Unknown").strip()
    mapping = TNS_INSTRUMENT_MAP.get(raw_inst, {})
    telescope = mapping.get("telescope") or telescope_hint or raw_inst
    instrument = mapping.get("instrument") or raw_inst
    obs_group_hint = mapping.get("obs_group")
    band = normalize_band_name(raw_inst, tns_filter or "Unknown")
    return ResolvedTnsPhotometry(
        telescope=telescope,
        instrument=instrument,
        band=band,
        obs_group_hint=obs_group_hint,
        tns_instrument=raw_inst,
        tns_filter=tns_filter or "",
    )


def ensure_yse_photometry_stack(
    user,
    *,
    telescope_name: str,
    instrument_name: str,
    band_name: str,
    obs_group_name: Optional[str] = None,
):
    """
    get_or_create Observatory / Telescope / Instrument / PhotometricBand for ingest.
    Returns (obs_group, instrument, band) model instances.
    """
    from YSE_App.models import (
        Instrument,
        Observatory,
        ObservationGroup,
        PhotometricBand,
        Telescope,
    )

    audit = {"created_by_id": user.id, "modified_by_id": user.id}
    if obs_group_name:
        obs_group, _ = ObservationGroup.objects.get_or_create(
            name=obs_group_name, defaults=audit
        )
    else:
        obs_group, _ = ObservationGroup.objects.get_or_create(
            name="Unknown", defaults=audit
        )

    observatory, _ = Observatory.objects.get_or_create(
        name=f"TNS-{telescope_name}"[:64],
        defaults={"utc_offset": 0, "tz_name": "UTC", **audit},
    )
    telescope, _ = Telescope.objects.get_or_create(
        name=telescope_name,
        defaults={
            "observatory": observatory,
            "latitude": 0.0,
            "longitude": 0.0,
            "elevation": 0.0,
            **audit,
        },
    )
    instrument, _ = Instrument.objects.get_or_create(
        name=instrument_name,
        defaults={"telescope": telescope, **audit},
    )
    band, _ = PhotometricBand.objects.get_or_create(
        name=band_name,
        instrument=instrument,
        defaults={
            "disp_color": "#888888",
            "disp_symbol": "circle",
            **audit,
        },
    )
    return obs_group, instrument, band


def lookup_instrument_band(
    user,
    instrument_name: str,
    band_name: str,
    obs_group_name: Optional[str] = None,
):
    """
    Return (obs_group, instrument, band), creating telescope/instrument/band if needed.
    """
    from YSE_App.models import Instrument, ObservationGroup, PhotometricBand

    resolved = resolve_tns_photometry(instrument_name, band_name)
    og_name = obs_group_name or resolved.obs_group_hint
    audit = {"created_by_id": user.id, "modified_by_id": user.id}
    if og_name:
        obs_group, _ = ObservationGroup.objects.get_or_create(
            name=og_name, defaults=audit
        )
    else:
        obs_group = ObservationGroup.objects.filter(name="Unknown").first()
        if not obs_group:
            obs_group, _ = ObservationGroup.objects.get_or_create(
                name="Unknown", defaults=audit
            )

    instrument = Instrument.objects.filter(name=resolved.instrument).first()
    if not instrument:
        _, instrument, band = ensure_yse_photometry_stack(
            user,
            telescope_name=resolved.telescope,
            instrument_name=resolved.instrument,
            band_name=resolved.band,
            obs_group_name=og_name,
        )
        return obs_group, instrument, band

    band = PhotometricBand.objects.filter(
        name=resolved.band, instrument=instrument
    ).first()
    if not band:
        band, _ = PhotometricBand.objects.get_or_create(
            name=resolved.band,
            instrument=instrument,
            defaults={
                "disp_color": "#888888",
                "disp_symbol": "circle",
                **audit,
            },
        )
    return obs_group, instrument, band
