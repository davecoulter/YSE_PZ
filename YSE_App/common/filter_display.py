"""
Canonical filter colors (Swope / PS1 uBVgrizy) and telescope symbol shapes for LC plots.

Filter names like r-ZTF, r-WFT, and Swope r map to the same color. Telescope families
(ZTF, PS1, Swope, …) share a Bokeh marker shape regardless of filter.
"""

from __future__ import annotations

# Swope / PS1 uBVgrizy palette (matches YSE_App_photometricband seed values).
FILTER_COLORS = {
    'u': '#ff7f0e',
    'B': '#1f77b4',
    'V': '#8FBC8F',
    'g': '#008000',
    'r': '#DC143C',
    'i': '#8c465b',
    'z': '#800080',
    'y': '#C9A227',
    'w': '#EBBE0C',
}

# Lowercase alias -> canonical filter key in FILTER_COLORS.
FILTER_ALIASES = {
    'u': 'u',
    'up': 'u',
    'u-johnson': 'u',
    'u-ps1': 'u',
    'b': 'B',
    'b-johnson': 'B',
    'v': 'V',
    'v-johnson': 'V',
    'v-crts': 'V',
    'v-crts-crts': 'V',
    'g': 'g',
    'gp': 'g',
    'g-ztf': 'g',
    'g-wft': 'g',
    'g-sloan': 'g',
    'g-ptf': 'g',
    'g-sm': 'g',
    'g-sm-skymapper': 'g',
    'cyan': 'g',
    'cyan-atlas': 'g',
    'r': 'r',
    'rp': 'r',
    'r-ztf': 'r',
    'r-wft': 'r',
    'r-sloan': 'r',
    'r-ptf': 'r',
    'r-cousins': 'r',
    'r-sm-skymapper': 'r',
    'orange': 'r',
    'orange-atlas': 'r',
    'i': 'i',
    'ip': 'i',
    'i-ztf': 'i',
    'i-sloan': 'i',
    'i-ptf': 'i',
    'i-cousins': 'i',
    'z': 'z',
    'zp': 'z',
    'z-sloan': 'z',
    'y': 'y',
    'y-ps1': 'y',
    'w': 'w',
    'w-ps1': 'w',
}

_BASE_FILTER_KEYS = frozenset({'u', 'b', 'v', 'g', 'r', 'i', 'z', 'y', 'w', 'up', 'gp', 'rp', 'ip', 'zp'})

# Instrument / telescope name substrings -> short legend label (e.g. ZTF-Cam -> ZTF).
TELESCOPE_SHORT_LABELS = (
    (('ztf', 'uvot'), 'ZTF'),
    (('gpc1', 'ps1', 'pan-starrs', 'panstarrs'), 'PS1'),
    (('swope',), 'Swope'),
    (('acam', 'atlas'), 'ATLAS'),
    (('direct', 'p200'), 'P200'),
    (('sinistro', 'pixis', 'lco', 'lcogt'), 'LCO'),
    (('acp', 'decam'), 'DECam'),
    (('sta1600', 'soar'), 'SOAR'),
    (('ptf',), 'PTF'),
    (('hst', 'acs', 'wfc3'), 'HST'),
)

# Instrument / telescope name substrings -> Bokeh glyph.
TELESCOPE_SYMBOL_RULES = (
    (('ztf',), 'diamond'),
    (('gpc1', 'ps1', 'pan-starrs', 'panstarrs'), 'square'),
    (('swope',), 'circle'),
    (('acam', 'atlas'), 'asterisk'),
    (('direct', 'p200'), 'hex'),
    (('sinistro', 'pixis', 'lco', 'lcogt'), 'dash'),
    (('acp', 'decam', 'decam'), 'star'),
    (('soar', 'sta1600'), 'triangle'),
    (('ptf',), 'cross'),
    (('swift', 'uvot'), 'diamond'),
    (('hst', 'wfc3', 'acs'), 'square'),
)

_FALLBACK_COLORS = ('#8dd3c7', '#bebada', '#fb8072', '#80b1d3', '#fdb462', '#b3de69', '#fccde5', '#d9d9d9')


def normalize_filter_name(band_name: str | None) -> str | None:
    """Map a band name (e.g. r-ZTF, r-WFT, g-Sloan) to a canonical uBVgrizy key."""
    if not band_name:
        return None
    lower = band_name.strip().lower()
    if lower in FILTER_ALIASES:
        return FILTER_ALIASES[lower]
    if 'cyan' in lower:
        return 'g'
    if 'orange' in lower:
        return 'r'
    base = lower.split('-')[0]
    if base in _BASE_FILTER_KEYS:
        return FILTER_ALIASES.get(base, base)
    if base == 'b':
        return 'B'
    if base == 'v':
        return 'V'
    return None


def band_display_color(
    band_name: str | None,
    disp_color: str | None = None,
    *,
    fallback_index: int = 0,
) -> str:
    """Resolve plot color: canonical filter family first, then DB value, then palette."""
    canonical = normalize_filter_name(band_name)
    if canonical and canonical in FILTER_COLORS:
        return FILTER_COLORS[canonical]
    if disp_color and disp_color != 'None':
        return disp_color
    return _FALLBACK_COLORS[fallback_index % len(_FALLBACK_COLORS)]


def telescope_display_symbol(
    instrument_name: str | None,
    disp_symbol: str | None = None,
) -> str:
    """Resolve Bokeh marker from telescope family (shape groups by instrument)."""
    inst_lower = (instrument_name or '').lower()
    for patterns, symbol in TELESCOPE_SYMBOL_RULES:
        if any(pat in inst_lower for pat in patterns):
            return symbol
    if disp_symbol and disp_symbol not in (None, 'None', 'inverted_triangle'):
        return disp_symbol
    return 'triangle'


def display_filter_label(band_name: str | None) -> str:
    """Short plot label (e.g. r-ZTF -> r). DB band name unchanged."""
    canonical = normalize_filter_name(band_name)
    if canonical:
        return canonical
    if band_name:
        return band_name.strip()
    return '?'


def telescope_display_name(
    instrument_name: str | None = None,
    telescope_name: str | None = None,
) -> str:
    """Short telescope family label for plot legends (e.g. ZTF-Cam -> ZTF)."""
    for candidate in (telescope_name, instrument_name):
        if not candidate or not str(candidate).strip():
            continue
        lower = str(candidate).strip().lower()
        for patterns, label in TELESCOPE_SHORT_LABELS:
            if any(pat in lower for pat in patterns):
                return label
        return str(candidate).strip()
    return 'Unknown'


def plot_legend_label(
    band_name: str | None,
    *,
    instrument_name: str | None = None,
    telescope_name: str | None = None,
) -> str:
    """Legend text: telescope + short filter (e.g. 'ZTF r')."""
    tel = telescope_display_name(instrument_name, telescope_name)
    filt = display_filter_label(band_name)
    return f'{tel} {filt}'


def filter_color_groups_for_display() -> list[dict]:
    """Human-readable color groups for docs / chat (filter family -> example names)."""
    groups = []
    examples = {
        'u': ['u', 'u-PS1', 'up (Sinistro)'],
        'B': ['B', 'B-Johnson'],
        'V': ['V', 'V-Johnson', 'V-crts'],
        'g': ['g', 'g-ZTF', 'g-WFT', 'g-Sloan', 'g-PTF', 'cyan-ATLAS'],
        'r': ['r', 'r-ZTF', 'r-WFT', 'r-Sloan', 'R-Cousins', 'orange-ATLAS'],
        'i': ['i', 'i-ZTF', 'i-Sloan', 'I-Cousins', 'ip'],
        'z': ['z', 'z-Sloan', 'zp'],
        'y': ['y', 'y-PS1'],
        'w': ['w', 'w-PS1'],
    }
    for key, color in FILTER_COLORS.items():
        groups.append({
            'filter': key,
            'color': color,
            'examples': examples.get(key, [key]),
        })
    return groups


def telescope_symbol_groups_for_display() -> list[dict]:
    """Human-readable telescope -> symbol groups."""
    labels = {
        'diamond': 'ZTF, Swift/UVOT',
        'square': 'PS1 (GPC1), HST',
        'circle': 'Swope',
        'asterisk': 'ATLAS (ACAM)',
        'hex': 'P200 Direct',
        'dash': 'LCO Sinistro / PIXIS',
        'star': 'DECam (ACP)',
        'triangle': 'SOAR / STA1600 (default fallback)',
        'cross': 'PTF',
    }
    seen = {}
    for _patterns, symbol in TELESCOPE_SYMBOL_RULES:
        seen.setdefault(symbol, labels.get(symbol, symbol))
    return [{'symbol': sym, 'telescopes': desc} for sym, desc in seen.items()]
