"""
Tests for the KMZ parser service.

The parser is a pure, synchronous function:
    parse_kmz(data: bytes) -> dict  (a GeoJSON FeatureCollection)

These tests build KMZ files in-memory (a ZIP containing a .kml) so they have
no dependency on the database, OSS, or the async HTTP harness.
"""
import io
import zipfile

import pytest

from app.services.kmz_parser import parse_kmz, KMZParseError


def make_kmz(kml: str, kml_name: str = "doc.kml", extra_files: dict | None = None) -> bytes:
    """Build an in-memory KMZ (zipped KML) and return its bytes."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(kml_name, kml)
        for name, content in (extra_files or {}).items():
            zf.writestr(name, content)
    return buf.getvalue()


KML_DOC = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    {body}
  </Document>
</kml>"""


def test_single_point_placemark():
    """A KMZ with one Point placemark yields one GeoJSON Point feature with
    longitude-first coordinates and the placemark's name + description."""
    kml = KML_DOC.format(body="""
      <Placemark>
        <name>Main Gate</name>
        <description>Primary entrance to the lot</description>
        <Point>
          <coordinates>120.9842,14.5995,0</coordinates>
        </Point>
      </Placemark>
    """)

    result = parse_kmz(make_kmz(kml))

    assert result["type"] == "FeatureCollection"
    assert len(result["features"]) == 1

    feature = result["features"][0]
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Point"
    # KML coordinates are lon,lat[,alt]; GeoJSON is [lon, lat] -- longitude first.
    assert feature["geometry"]["coordinates"] == [120.9842, 14.5995]

    props = feature["properties"]
    assert props["name"] == "Main Gate"
    assert props["description"] == "Primary entrance to the lot"
    assert props["geometry_type"] == "Point"


def test_polygon_placemark():
    """A Polygon placemark (a building footprint) yields a GeoJSON Polygon
    whose coordinates are a list of linear rings of [lon, lat] points."""
    kml = KML_DOC.format(body="""
      <Placemark>
        <name>Building A</name>
        <description>Main hotel block</description>
        <Polygon>
          <outerBoundaryIs>
            <LinearRing>
              <coordinates>
                120.9840,14.5990,0 120.9845,14.5990,0 120.9845,14.5995,0 120.9840,14.5990,0
              </coordinates>
            </LinearRing>
          </outerBoundaryIs>
        </Polygon>
      </Placemark>
    """)

    result = parse_kmz(make_kmz(kml))

    assert len(result["features"]) == 1
    feature = result["features"][0]
    assert feature["geometry"]["type"] == "Polygon"
    assert feature["properties"]["geometry_type"] == "Polygon"
    assert feature["properties"]["name"] == "Building A"
    # GeoJSON Polygon coordinates: an array of rings; the outer ring first.
    rings = feature["geometry"]["coordinates"]
    assert len(rings) == 1
    assert rings[0][0] == [120.9840, 14.5990]
    assert rings[0][2] == [120.9845, 14.5995]
    assert len(rings[0]) == 4


def test_linestring_placemark():
    """A LineString placemark (an access road / infra) yields a GeoJSON
    LineString whose coordinates are an array of [lon, lat] points."""
    kml = KML_DOC.format(body="""
      <Placemark>
        <name>Access Road</name>
        <description>Paved road from highway</description>
        <LineString>
          <coordinates>
            120.9830,14.5980,0 120.9835,14.5985,0 120.9840,14.5990,0
          </coordinates>
        </LineString>
      </Placemark>
    """)

    result = parse_kmz(make_kmz(kml))

    feature = result["features"][0]
    assert feature["geometry"]["type"] == "LineString"
    assert feature["properties"]["geometry_type"] == "LineString"
    assert feature["properties"]["name"] == "Access Road"
    coords = feature["geometry"]["coordinates"]
    assert coords[0] == [120.9830, 14.5980]
    assert coords[-1] == [120.9840, 14.5990]
    assert len(coords) == 3


def test_placemarks_nested_in_folders_capture_folder_name():
    """Placemarks nested inside <Folder> elements are all found (recursive),
    and each feature records its containing folder name so the frontend can
    group Buildings / Infrastructure / Pins."""
    kml = KML_DOC.format(body="""
      <Folder>
        <name>Buildings</name>
        <Placemark>
          <name>Building A</name>
          <Polygon><outerBoundaryIs><LinearRing><coordinates>
            120.984,14.599,0 120.985,14.599,0 120.985,14.600,0 120.984,14.599,0
          </coordinates></LinearRing></outerBoundaryIs></Polygon>
        </Placemark>
      </Folder>
      <Folder>
        <name>Infrastructure</name>
        <Placemark>
          <name>Access Road</name>
          <LineString><coordinates>120.983,14.598,0 120.984,14.599,0</coordinates></LineString>
        </Placemark>
      </Folder>
      <Placemark>
        <name>Lot Marker</name>
        <Point><coordinates>120.9842,14.5995,0</coordinates></Point>
      </Placemark>
    """)

    result = parse_kmz(make_kmz(kml))

    assert len(result["features"]) == 3
    by_name = {f["properties"]["name"]: f["properties"] for f in result["features"]}
    assert by_name["Building A"]["folder"] == "Buildings"
    assert by_name["Access Road"]["folder"] == "Infrastructure"
    # A placemark at the document root (no enclosing folder) has folder None.
    assert by_name["Lot Marker"]["folder"] is None


def test_kml_not_named_doc_kml_prefers_root_level():
    """The main KML inside a KMZ is not guaranteed to be 'doc.kml'. The parser
    uses the root-level .kml file, ignoring .kml assets nested in subfolders."""
    main_kml = KML_DOC.format(body="""
      <Placemark>
        <name>Real Marker</name>
        <Point><coordinates>120.9842,14.5995,0</coordinates></Point>
      </Placemark>
    """)
    nested_kml = KML_DOC.format(body="""
      <Placemark>
        <name>Decoy Marker</name>
        <Point><coordinates>0,0,0</coordinates></Point>
      </Placemark>
    """)

    data = make_kmz(
        main_kml,
        kml_name="My Property Map.kml",
        extra_files={"layers/overlay.kml": nested_kml},
    )

    result = parse_kmz(data)

    names = [f["properties"]["name"] for f in result["features"]]
    assert names == ["Real Marker"]


def test_cdata_html_description_preserved():
    """Descriptions are often wrapped in CDATA with HTML markup (Google Earth
    exports balloons this way). The HTML content must be preserved intact."""
    kml = KML_DOC.format(body="""
      <Placemark>
        <name>Clubhouse</name>
        <description><![CDATA[<b>Clubhouse</b><br/>Built 2021. <a href="http://x">plan</a>]]></description>
        <Point><coordinates>120.9842,14.5995,0</coordinates></Point>
      </Placemark>
    """)

    result = parse_kmz(make_kmz(kml))

    desc = result["features"][0]["properties"]["description"]
    assert desc == '<b>Clubhouse</b><br/>Built 2021. <a href="http://x">plan</a>'


def test_parses_kml_without_namespace():
    """Some real-world KML omits the xmlns declaration. Parsing must not depend
    on the default KML namespace being present."""
    kml = """<?xml version="1.0" encoding="UTF-8"?>
    <kml>
      <Document>
        <Placemark>
          <name>No NS Marker</name>
          <Point><coordinates>120.9842,14.5995,0</coordinates></Point>
        </Placemark>
      </Document>
    </kml>"""

    result = parse_kmz(make_kmz(kml))

    assert len(result["features"]) == 1
    assert result["features"][0]["properties"]["name"] == "No NS Marker"
    assert result["features"][0]["geometry"]["coordinates"] == [120.9842, 14.5995]


def test_non_zip_payload_raises():
    """Bytes that are not a ZIP archive raise a clear KMZParseError."""
    with pytest.raises(KMZParseError):
        parse_kmz(b"this is not a zip file")


def test_archive_without_kml_raises():
    """A ZIP that contains no .kml document raises KMZParseError."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("readme.txt", "no kml here")
    with pytest.raises(KMZParseError):
        parse_kmz(buf.getvalue())


def test_malformed_kml_xml_raises():
    """A KMZ whose KML is not well-formed XML raises KMZParseError rather than
    leaking a low-level XML parse error."""
    data = make_kmz("<kml><Document><Placemark></broken>")
    with pytest.raises(KMZParseError):
        parse_kmz(data)


def test_multigeometry_placemark():
    """Google Earth often wraps several geometries for one placemark in a
    <MultiGeometry>. These yield a single feature with a GeometryCollection so
    no geometry is silently dropped."""
    kml = KML_DOC.format(body="""
      <Placemark>
        <name>Hotel Complex</name>
        <description>Tower plus footprint</description>
        <MultiGeometry>
          <Point><coordinates>120.9842,14.5995,0</coordinates></Point>
          <Polygon><outerBoundaryIs><LinearRing><coordinates>
            120.984,14.599,0 120.985,14.599,0 120.985,14.600,0 120.984,14.599,0
          </coordinates></LinearRing></outerBoundaryIs></Polygon>
        </MultiGeometry>
      </Placemark>
    """)

    result = parse_kmz(make_kmz(kml))

    assert len(result["features"]) == 1
    feature = result["features"][0]
    assert feature["properties"]["name"] == "Hotel Complex"
    assert feature["geometry"]["type"] == "GeometryCollection"
    assert feature["properties"]["geometry_type"] == "GeometryCollection"
    geoms = feature["geometry"]["geometries"]
    assert [g["type"] for g in geoms] == ["Point", "Polygon"]
    assert geoms[0]["coordinates"] == [120.9842, 14.5995]


def test_malformed_coordinates_raise_kmz_parse_error():
    """A placemark whose coordinates are not parseable numbers raises
    KMZParseError (surfaced as a clean 422) rather than leaking a ValueError
    that would become a 500."""
    kml = KML_DOC.format(body="""
      <Placemark>
        <name>Broken</name>
        <Point><coordinates>not,a,number</coordinates></Point>
      </Placemark>
    """)
    with pytest.raises(KMZParseError):
        parse_kmz(make_kmz(kml))


def test_empty_kml_returns_empty_collection():
    """A valid KML with no placemarks is not an error -- it yields an empty
    FeatureCollection."""
    result = parse_kmz(make_kmz(KML_DOC.format(body="")))
    assert result == {"type": "FeatureCollection", "features": []}
