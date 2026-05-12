"""
Static mapping from free-text country names found in `geography.country`
to ISO 3166-1 alpha-2 codes. Used by the Geography stats tab to plot
set-place data on a world choropleth.

Lookup is case-insensitive (.lower() both sides).

For the reverse direction (ISO → list of free-text variants), use
`iso_to_country_names(iso)`. That's how /api/stats/films-by-country
finds all geography rows for a given country when the user clicks the
map.
"""

from __future__ import annotations

from collections import defaultdict

# Map (free-text country names found in `geography.country`) → ISO alpha-2.
# Includes common variants/aliases. Names with historical scope (Soviet Union,
# West Germany) are intentionally folded into the modern successor's code so
# the choropleth still has somewhere to display them.

COUNTRY_NAME_TO_ISO: dict[str, str] = {
    # North America
    "united states": "US",
    "united states of america": "US",
    "usa": "US",
    "us": "US",
    "canada": "CA",
    "mexico": "MX",

    # United Kingdom & constituent nations
    "united kingdom": "GB",
    "uk": "GB",
    "great britain": "GB",
    "britain": "GB",
    "england": "GB",
    "scotland": "GB",
    "wales": "GB",
    "northern ireland": "GB",

    # Western & Northern Europe
    "france": "FR",
    "germany": "DE",
    "west germany": "DE",
    "east germany": "DE",
    "italy": "IT",
    "spain": "ES",
    "portugal": "PT",
    "belgium": "BE",
    "netherlands": "NL",
    "the netherlands": "NL",
    "holland": "NL",
    "luxembourg": "LU",
    "switzerland": "CH",
    "austria": "AT",
    "ireland": "IE",
    "denmark": "DK",
    "sweden": "SE",
    "norway": "NO",
    "finland": "FI",
    "iceland": "IS",

    # Central & Eastern Europe
    "poland": "PL",
    "czech republic": "CZ",
    "czechia": "CZ",
    "czechoslovakia": "CZ",
    "slovakia": "SK",
    "hungary": "HU",
    "romania": "RO",
    "bulgaria": "BG",
    "greece": "GR",
    "croatia": "HR",
    "serbia": "RS",
    "yugoslavia": "RS",
    "slovenia": "SI",
    "bosnia and herzegovina": "BA",
    "north macedonia": "MK",
    "macedonia": "MK",
    "albania": "AL",
    "kosovo": "XK",
    "montenegro": "ME",
    "turkey": "TR",
    "ukraine": "UA",
    "russia": "RU",
    "soviet union": "RU",
    "ussr": "RU",
    "belarus": "BY",
    "estonia": "EE",
    "latvia": "LV",
    "lithuania": "LT",
    "moldova": "MD",
    "georgia": "GE",
    "armenia": "AM",
    "azerbaijan": "AZ",

    # East & Southeast Asia
    "china": "CN",
    "hong kong": "HK",
    "macau": "MO",
    "taiwan": "TW",
    "japan": "JP",
    "south korea": "KR",
    "korea": "KR",
    "north korea": "KP",
    "mongolia": "MN",
    "thailand": "TH",
    "vietnam": "VN",
    "cambodia": "KH",
    "laos": "LA",
    "myanmar": "MM",
    "burma": "MM",
    "indonesia": "ID",
    "malaysia": "MY",
    "philippines": "PH",
    "singapore": "SG",
    "brunei": "BN",
    "east timor": "TL",

    # South Asia
    "india": "IN",
    "pakistan": "PK",
    "bangladesh": "BD",
    "sri lanka": "LK",
    "nepal": "NP",
    "bhutan": "BT",
    "afghanistan": "AF",

    # Middle East
    "iran": "IR",
    "iraq": "IQ",
    "israel": "IL",
    "palestine": "PS",
    "lebanon": "LB",
    "syria": "SY",
    "jordan": "JO",
    "saudi arabia": "SA",
    "united arab emirates": "AE",
    "uae": "AE",
    "qatar": "QA",
    "kuwait": "KW",
    "yemen": "YE",
    "oman": "OM",
    "bahrain": "BH",

    # Africa
    "egypt": "EG",
    "morocco": "MA",
    "algeria": "DZ",
    "tunisia": "TN",
    "libya": "LY",
    "sudan": "SD",
    "south africa": "ZA",
    "nigeria": "NG",
    "kenya": "KE",
    "ethiopia": "ET",
    "ghana": "GH",
    "senegal": "SN",
    "ivory coast": "CI",
    "cote d'ivoire": "CI",
    "côte d'ivoire": "CI",
    "rwanda": "RW",
    "uganda": "UG",
    "tanzania": "TZ",
    "zimbabwe": "ZW",
    "zambia": "ZM",
    "botswana": "BW",
    "namibia": "NA",
    "mozambique": "MZ",
    "angola": "AO",
    "mali": "ML",
    "burkina faso": "BF",
    "niger": "NE",
    "cameroon": "CM",
    "chad": "TD",
    "madagascar": "MG",
    "mauritania": "MR",
    "somalia": "SO",
    "democratic republic of the congo": "CD",
    "dr congo": "CD",
    "congo": "CG",
    "republic of the congo": "CG",

    # Caribbean
    "cuba": "CU",
    "jamaica": "JM",
    "haiti": "HT",
    "dominican republic": "DO",
    "puerto rico": "PR",
    "trinidad and tobago": "TT",
    "barbados": "BB",
    "bahamas": "BS",

    # Latin America
    "brazil": "BR",
    "argentina": "AR",
    "chile": "CL",
    "colombia": "CO",
    "venezuela": "VE",
    "peru": "PE",
    "bolivia": "BO",
    "ecuador": "EC",
    "uruguay": "UY",
    "paraguay": "PY",
    "guatemala": "GT",
    "honduras": "HN",
    "nicaragua": "NI",
    "el salvador": "SV",
    "costa rica": "CR",
    "panama": "PA",

    # Oceania
    "australia": "AU",
    "new zealand": "NZ",
    "papua new guinea": "PG",
    "fiji": "FJ",
}


# Canonical English name per ISO code (first occurrence wins, but for clarity
# we set explicit preferences here so e.g. "United States" beats "USA").
_PREFERRED_NAME_BY_ISO: dict[str, str] = {
    "US": "United States",
    "GB": "United Kingdom",
    "DE": "Germany",
    "RU": "Russia",
    "NL": "Netherlands",
    "CZ": "Czech Republic",
    "MM": "Myanmar",
    "CI": "Ivory Coast",
    "MK": "North Macedonia",
    "CD": "Democratic Republic of the Congo",
    "CG": "Republic of the Congo",
    "AE": "United Arab Emirates",
    "KR": "South Korea",
    "KP": "North Korea",
}


def country_name_to_iso(name: str | None) -> str | None:
    """Return ISO 3166-1 alpha-2 code for a free-text country name, or None.

    Case-insensitive lookup. Strips surrounding whitespace.
    """
    if not name:
        return None
    return COUNTRY_NAME_TO_ISO.get(name.strip().lower())


def preferred_country_name(iso: str) -> str:
    """Canonical English display name for an ISO alpha-2 code.

    Falls back to title-casing the first matching free-text variant if the
    ISO isn't in the explicit preference list.
    """
    if iso in _PREFERRED_NAME_BY_ISO:
        return _PREFERRED_NAME_BY_ISO[iso]
    for name, code in COUNTRY_NAME_TO_ISO.items():
        if code == iso:
            return name.title()
    return iso  # unknown — return the code itself


# Reverse map: ISO → list of all free-text variants that resolve to it.
# Used by /api/stats/films-by-country?type=set_place to find every geography
# row for a country when the user clicks the map.
_ISO_TO_NAMES: dict[str, list[str]] = defaultdict(list)
for _name, _iso in COUNTRY_NAME_TO_ISO.items():
    _ISO_TO_NAMES[_iso].append(_name)


def iso_to_country_names(iso: str) -> list[str]:
    """Return all lowercase free-text variants that map to this ISO code."""
    return list(_ISO_TO_NAMES.get(iso.upper(), []))


# Legacy / defunct ISO codes that TMDB sometimes still emits, mapped to the
# modern successor state's alpha-2. Used to fold pre-1991 productions into
# their current geographies for the world map.
LEGACY_ISO_ALIASES: dict[str, str] = {
    "SU": "RU",  # Soviet Union → Russia
    "YU": "RS",  # Yugoslavia (1945-1992) → Serbia (chosen as historical core)
    "CS": "CZ",  # Czechoslovakia → Czech Republic
    "DD": "DE",  # East Germany → Germany
}


def normalize_iso(iso: str | None) -> str | None:
    """Fold legacy ISO codes into their modern successor.

    Returns the upper-cased ISO unchanged if it isn't a legacy code.
    """
    if not iso:
        return None
    upper = iso.upper()
    return LEGACY_ISO_ALIASES.get(upper, upper)
