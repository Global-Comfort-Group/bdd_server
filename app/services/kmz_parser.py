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


def _placemark_to_feature(placemark: ET.Element, folder: str | None) -> dict[str, Any] | None:
    try:
        geometry = _extract_geometry(placemark)
    except (ValueError, IndexError) as exc:
        name = _text(_find_child(placemark, "name")) or "<unnamed>"
        raise KMZParseError(f"Invalid coordinates in placemark '{name}': {exc}") from exc
    if geometry is None:
        return None

    return {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "name": _text(_find_child(placemark, "name")),
            "description": _text(_find_child(placemark, "description")),
            "geometry_type": geometry["type"],
            "folder": folder,
        },
    }


def _collect_features(element: ET.Element, folder: str | None, out: list[dict[str, Any]]) -> None:
    """Recursively walk Document/Folder containers, collecting placemark
    features and tracking the name of the nearest enclosing <Folder>."""
    for child in element:
        tag = _localname(child.tag)
        if tag == "Placemark":
            feature = _placemark_to_feature(child, folder)
            if feature is not None:
                out.append(feature)
        elif tag == "Folder":
            child_folder = _text(_find_child(child, "name")) or folder
            _collect_features(child, child_folder, out)
        elif tag == "Document":
            _collect_features(child, folder, out)


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

    features: list[dict[str, Any]] = []
    _collect_features(root, None, features)

    return {"type": "FeatureCollection", "features": features}
