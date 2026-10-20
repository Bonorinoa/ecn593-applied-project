"""World Bank API v2 fetcher for the external anchor vector z.

Design notes
------------
- Keyless JSON API. Only the small summary is committed (data/anchors.json,
  via scripts/fetch_anchors.py). A fetch today serves newer values.
- We use mrnev=1 (most recent non-empty value per country) so every country
  contributes its latest observation rather than a fixed calendar year.
- Aggregates are meant to be excluded (config.AGGREGATE_NAMES_EXCLUDED), but that
  list has only 9 names; the API serves more regional and income groups, and
  those are still counted. Known limitation of the archived run (PLAN item 14).
"""
import json
import urllib.request

from . import config


def _fetch_indicator(code: str, per_page: int = 400) -> list[dict]:
    """Return raw indicator rows from the World Bank API (page 1 is enough at
    per_page=400 for ~250 countries x 1 value)."""
    url = f"{config.WB_BASE}/country/all/indicator/{code}?format=json&per_page={per_page}&mrnev=1"
    req = urllib.request.Request(url, headers={"User-Agent": "poc-abm/0.1 (research)"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode())
    meta, rows = payload[0], payload[1]
    if meta.get("pages", 1) > 1:
        raise RuntimeError(f"{code}: unexpected pagination (pages={meta['pages']})")
    return rows


def _country_values(rows: list[dict]) -> dict[str, float]:
    """country -> most-recent value, aggregates excluded."""
    out = {}
    for r in rows:
        name = r["country"]["value"]
        if name in config.AGGREGATE_NAMES_EXCLUDED:
            continue
        v = r.get("value")
        if v is not None:
            out[name] = float(v)
    return out


def build_anchors() -> dict:
    """Compute the anchor vector z and everything needed to audit it.

    Returns a dict with per-indicator stats plus the final z components.
    """
    import numpy as np

    imm = _country_values(_fetch_indicator(config.WB_INDICATORS["immunization"]))
    edu = _country_values(_fetch_indicator(config.WB_INDICATORS["sec_completion"]))
    net = _country_values(_fetch_indicator(config.WB_INDICATORS["internet"]))

    # gradient anchor: cross-country OLS slope of immunization on secondary completion,
    # standardized -> correlation. This is the "education gradient of preventive
    # behavior" the ABM must reproduce via corr(Y_T, x_education).
    common = sorted(set(imm) & set(edu))
    a = np.array([imm[c] for c in common])
    b = np.array([edu[c] for c in common])
    corr_grad = float(np.corrcoef(a, b)[0, 1])

    anchors = {
        "level_immunization_mean": float(np.mean(list(imm.values()))),
        "gradient_edu_corr": corr_grad,
        "level_internet_mean": float(np.mean(list(net.values()))),
        "_audit": {
            "n_immunization": len(imm),
            "n_completion": len(edu),
            "n_overlap_gradient": len(common),
            "n_internet": len(net),
            "sd_immunization": float(np.std(list(imm.values()))),
            "mean_completion": float(np.mean(b)),
            "sd_internet": float(np.std(list(net.values()))),
        },
    }
    return anchors


if __name__ == "__main__":
    print(json.dumps(build_anchors(), indent=2))
