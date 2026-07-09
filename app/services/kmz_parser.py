"""
KMZ -> GeoJSON parser.

A KMZ is a ZIP archive containing a KML document (XML) plus optional assets.
This module extracts the KML and converts its placemarks into a GeoJSON
FeatureCollection that the frontend can render directly with Google Maps'
``map.data.addGeoJson(...)``.

Pure and synchronous: no database, OSS, or network access.
"""
import zipfile
import io
import xml.etree.ElementTree as ET
from typing import Any


class KMZParseError(Exception):
    """Raised when a KMZ/KML payload cannot be parsed."""


def _localname(tag: str) -> str:
    """Return an element's tag without its XML namespace prefix.

    KML files may declare ``xmlns="http://www.opengis.net/kml/2.2"`` (or a
    different/absent namespace). Matching on the local name keeps parsing
    robust regardless of the namespace in use.
    """
    return tag.rsplit("}", 1)[-1]


def _find_child(element: ET.Element, name: str) -> ET.Element | None:
    for child in element:
        if _localname(child.tag) == name:
            return child
    return None


def _text(element: ET.Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    return element.text.strip() or None


def _parse_coord_tuple(raw: str) -> list[float]:
    """Parse a single ``lon,lat[,alt]`` token into ``[lon, lat]``."""
    parts = raw.split(",")
    lon = float(parts[0])
    lat = float(parts[1])
    return [lon, lat]


def _parse_coord_list(raw: str) -> list[list[float]]:
    """Parse whitespace-separated ``lon,lat[,alt]`` tokens into [[lon, lat], ...]."""
    return [_parse_coord_tuple(token) for token in raw.split()]


def _find_descendant(element: ET.Element, name: str) -> ET.Element | None:
    for descendant in element.iter():
        if _localname(descendant.tag) == name:
            return descendant
    return None


_GEOMETRY_TAGS = ("Point", "LineString", "Polygon", "MultiGeometry")


def _geometry_from_element(element: ET.Element) -> dict[str, Any] | None:
    """Convert a single KML geometry element into a GeoJSON geometry dict."""
    tag = _localname(element.tag)

    if tag == "Point":
        coords_text = _text(_find_child(element, "coordinates"))
        if not coords_text:
            return None
        return {"type": "Point", "coordinates": _parse_coord_tuple(coords_text.split()[0])}

    if tag == "LineString":
        coords_text = _text(_find_child(element, "coordinates"))
        if not coords_text:
            return None
        return {"type": "LineString", "coordinates": _parse_coord_list(coords_text)}

    if tag == "Polygon":
        outer = _find_descendant(element, "outerBoundaryIs")
        ring_el = _find_descendant(outer, "coordinates") if outer is not None else None
        coords_text = _text(ring_el)
        if not coords_text:
            return None
        return {"type": "Polygon", "coordinates": [_parse_coord_list(coords_text)]}

    if tag == "MultiGeometry":
        geometries = []
        for child in element:
            if _localname(child.tag) in _GEOMETRY_TAGS:
                geom = _geometry_from_element(child)
                if geom is not None:
                    geometries.append(geom)
        if not geometries:
            return None
        return {"type": "GeometryCollection", "geometries": geometries}

    return None


def _extract_geometry(placemark: ET.Element) -> dict[str, Any] | None:
    """Return a GeoJSON geometry dict for the placemark, or None if unsupported."""
    for child in placemark:
        if _localname(child.tag) in _GEOMETRY_TAGS:
            geometry = _geometry_from_element(child)
            if geometry is not None:
                return geometry
    return None


# --- Icon / style resolution -------------------------------------------------
#
# Google Earth placemarks reference an icon indirectly:
#   <Placemark><styleUrl>#msn_dining</styleUrl> ...
#   <StyleMap id="msn_dining"><Pair><key>normal</key><styleUrl>#sn_dining</styleUrl></Pair>...
#   <Style id="sn_dining"><IconStyle><scale>1.1</scale>
#       <Icon><href>http://maps.google.com/mapfiles/kml/shapes/dining.png</href></Icon>
#       <hotSpot x="0.5" y="0" xunits="fraction" yunits="fraction"/></IconStyle></Style>
#
# We resolve each placemark to its icon URL (+ scale + anchor) so the map can
# render the same icon the KMZ author picked in Google Earth, instead of a
# generic dot. Icons are Google-hosted URLs; we never store binary assets.

_ICON_MAX_STYLE_DEPTH = 5


def _icon_from_iconstyle(iconstyle: ET.Element) -> dict[str, Any] | None:
    """Extract ``{icon, scale, anchor}`` from an ``<IconStyle>``, or None.

    Only absolute http(s) hrefs are usable directly; ``http://`` is upgraded to
    ``https://`` to avoid mixed-content blocking on the HTTPS app. Relative
    (embedded-asset) hrefs are not served, so they yield None and the caller
    falls back to the default pin.
    """
    icon_el = _find_child(iconstyle, "Icon")
    href = _text(_find_child(icon_el, "href")) if icon_el is not None else None
    if not href:
        return None
    if href.startswith("http://"):
        href = "https://" + href[len("http://"):]
    elif not href.startswith("https://"):
        return None

    scale_text = _text(_find_child(iconstyle, "scale"))
    try:
        scale = float(scale_text) if scale_text else None
    except ValueError:
        scale = None

    anchor: dict[str, Any] | None = None
    hotspot = _find_child(iconstyle, "hotSpot")
    if hotspot is not None:
        try:
            anchor = {
                "x": float(hotspot.get("x", "0.5")),
                "y": float(hotspot.get("y", "0.5")),
                "xunits": hotspot.get("xunits", "fraction"),
                "yunits": hotspot.get("yunits", "fraction"),
            }
        except (ValueError, TypeError):
            anchor = None

    return {"icon": href, "scale": scale, "anchor": anchor}


def _icon_from_style_element(style: ET.Element) -> dict[str, Any] | None:
    iconstyle = _find_child(style, "IconStyle")
    return _icon_from_iconstyle(iconstyle) if iconstyle is not None else None


def _collect_style_index(root: ET.Element) -> tuple[dict[str, dict], dict[str, str]]:
    """Build ``{style_id -> icon info}`` and ``{stylemap_id -> normal style url}``
    from every ``<Style id>`` / ``<StyleMap id>`` anywhere in the document."""
    icon_styles: dict[str, dict] = {}
    style_maps: dict[str, str] = {}
    for el in root.iter():
        name = _localname(el.tag)
        el_id = el.get("id")
        if not el_id:
            continue
        if name == "Style":
            info = _icon_from_style_element(el)
            if info is not None:
                icon_styles[el_id] = info
        elif name == "StyleMap":
            for pair in el:
                if _localname(pair.tag) != "Pair":
                    continue
                if _text(_find_child(pair, "key")) == "normal":
                    normal_url = _text(_find_child(pair, "styleUrl"))
                    if normal_url:
                        style_maps[el_id] = normal_url.lstrip("#")
                    break
    return icon_styles, style_maps


def _resolve_icon(
    style_url: str | None,
    icon_styles: dict[str, dict],
    style_maps: dict[str, str],
    _depth: int = 0,
) -> dict[str, Any] | None:
    """Follow a ``styleUrl`` through StyleMaps to the icon it ultimately names."""
    if not style_url or _depth > _ICON_MAX_STYLE_DEPTH:
        return None
    key = style_url.lstrip("#")
    if key in icon_styles:
        return icon_styles[key]
    if key in style_maps:
        return _resolve_icon(style_maps[key], icon_styles, style_maps, _depth + 1)
    return None


def _placemark_to_feature(
    placemark: ET.Element,
    folder: str | None,
    icon_styles: dict[str, dict],
    style_maps: dict[str, str],
) -> dict[str, Any] | None:
    try:
        geometry = _extract_geometry(placemark)
    except (ValueError, IndexError) as exc:
        name = _text(_find_child(placemark, "name")) or "<unnamed>"
        raise KMZParseError(f"Invalid coordinates in placemark '{name}': {exc}") from exc
    if geometry is None:
        return None

    # Inline <Style> on the placemark wins; otherwise resolve its <styleUrl>.
    inline_style = _find_child(placemark, "Style")
    icon_info = _icon_from_style_element(inline_style) if inline_style is not None else None
    if icon_info is None:
        icon_info = _resolve_icon(
            _text(_find_child(placemark, "styleUrl")), icon_styles, style_maps
        )

    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "name": _text(_find_child(placemark, "name")),
            "description": _text(_find_child(placemark, "description")),
            "geometry_type": geometry["type"],
            "folder": folder,
            # Icon the KMZ author assigned in Google Earth (None -> default pin).
            "icon": icon_info["icon"] if icon_info else None,
            "icon_scale": icon_info["scale"] if icon_info else None,
            "icon_anchor": icon_info["anchor"] if icon_info else None,
        },
    }


def _collect_features(
    element: ET.Element,
    folder: str | None,
    out: list[dict[str, Any]],
    icon_styles: dict[str, dict],
    style_maps: dict[str, str],
) -> None:
    """Recursively walk Document/Folder containers, collecting placemark
    features and tracking the name of the nearest enclosing <Folder>."""
    for child in element:
        tag = _localname(child.tag)
        if tag == "Placemark":
            feature = _placemark_to_feature(child, folder, icon_styles, style_maps)
            if feature is not None:
                out.append(feature)
        elif tag == "Folder":
            child_folder = _text(_find_child(child, "name")) or folder
            _collect_features(child, child_folder, out, icon_styles, style_maps)
        elif tag == "Document":
            _collect_features(child, folder, out, icon_styles, style_maps)


def _extract_kml(data: bytes) -> str:
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise KMZParseError("File is not a valid KMZ archive") from exc

    kml_names = [n for n in archive.namelist() if n.lower().endswith(".kml")]
    if not kml_names:
        raise KMZParseError("KMZ archive contains no .kml document")

    # The main document is the root-level .kml (no path separator); .kml files
    # nested in subfolders are referenced assets/overlays. Fall back to the
    # first .kml if none sit at the root.
    root_level = [n for n in kml_names if "/" not in n]
    chosen = root_level[0] if root_level else kml_names[0]

    return archive.read(chosen).decode("utf-8")


def parse_kmz(data: bytes) -> dict[str, Any]:
    """Parse KMZ bytes into a GeoJSON FeatureCollection."""
    kml = _extract_kml(data)
    try:
        root = ET.fromstring(kml)
    except ET.ParseError as exc:
        raise KMZParseError(f"KML document is not well-formed XML: {exc}") from exc

    icon_styles, style_maps = _collect_style_index(root)

    features: list[dict[str, Any]] = []
    _collect_features(root, None, features, icon_styles, style_maps)

    return {"type": "FeatureCollection", "features": features}
