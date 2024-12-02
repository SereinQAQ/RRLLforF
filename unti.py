import ezdxf
from shapely.geometry import Polygon
from shapely.ops import unary_union


def dxf_to_polygon(dxf_path):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    polygons = []
    for entity in msp.query("LWPOLYLINE"):
        points = [tuple(p[:2]) for p in entity]
        polygons.append(Polygon(points))
    return unary_union(polygons)


def save_polygon_to_dxf(polygon, dxf_path):
    doc = ezdxf.new(dxfversion="R2010")
    msp = doc.modelspace()
    points = list(polygon.exterior.coords)
    msp.add_lwpolyline(points, close=True)
    doc.saveas(dxf_path)


def booll():

    polygon1 = dxf_to_polygon("docouter.dxf")
    polygon2 = dxf_to_polygon("docinter.dxf")

    result_polygon = polygon1.difference(polygon2)

    save_polygon_to_dxf(result_polygon, "result.dxf")
