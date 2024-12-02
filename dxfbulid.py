import ezdxf
from shapely.geometry import box
from shapely.ops import unary_union

# 创建两个新的DXF文件


l1 = 600
w1 = 800  # 竖着
l2 = 600
w2 = 800  # 竖着
l3 = 600
w3 = 800  # 竖着
l4 = 600
w4 = 800


class SquareOperations:
    def up_upsquare(self, coords, lw, up=True):
        x, y, yy = coords
        l, w = lw
        outer_square_x = x
        outer_square_y = y if up else yy
        outer_square_xx = outer_square_x + l
        outer_square_yy = outer_square_y + w if up else outer_square_y - w

        outer_square = box(
            outer_square_x, outer_square_y, outer_square_xx, outer_square_yy
        )
        center_x = outer_square_x + l / 2
        center_y = outer_square_y + w / 2 if up else outer_square_y - w / 2

        x1 = outer_square_xx
        y1 = outer_square_y if up else outer_square_yy
        yy1 = outer_square_yy if up else outer_square_y

        return outer_square, [x1, y1, yy1], [center_x, center_y]

    def plump(self, coords, lw, up):
        return self.up_upsquare(coords, lw, up)

    def flows(self, coords, lw, up):
        outer_square, coords_list, _ = self.up_upsquare(coords, lw, up)
        return outer_square, coords_list


class ShapeDrawer:
    def __init__(self, msp):
        self.msp = msp

    def add_square(self, center, dimensions):
        center_x, center_y = center
        l, w = dimensions

        square = box(
            center_x - l / 2,
            center_y - w / 2,
            center_x + l / 2,
            center_y + w / 2,
        )
        points = list(square.exterior.coords)
        self.msp.add_lwpolyline(points)

    def add_circle(self, center, radius):
        center_x, center_y = center
        self.msp.add_circle(center=(center_x, center_y), radius=radius)

    def add_ellipse(self, center, rho, radii=[180, 150]):
        center_x, center_y = center
        radius_x, radius_y = radii
        self.msp.add_ellipse(
            center=(center_x, center_y),  # 圆心坐标
            major_axis=(radius_x, rho),  # 主轴半径和方向
            ratio=radius_y / radius_x,  # 长短轴之比
        )

    def add_shape(self, shape_type, *args):
        if shape_type == "square":
            self.add_square(*args)
        elif shape_type == "circle":
            self.add_circle(*args)
        elif shape_type == "ellipse":
            self.add_ellipse(*args)
        else:
            raise ValueError(f"Unknown shape type: {shape_type}")


def add_polygon_to_dxf(msp, polygon):
    if polygon.geom_type == "Polygon":
        exterior_points = list(polygon.exterior.coords)
        msp.add_lwpolyline(exterior_points)
        for interior in polygon.interiors:
            interior_points = list(interior.coords)
            msp.add_lwpolyline(interior_points)


def doc_outerbuild(lis=[True,False]):
    # 创建 SquareOperations 类的实例

    doc_outer = ezdxf.new(dxfversion="R2010")
    msp_outer = doc_outer.modelspace()

    start_x = 0
    start_y = 0
    H1 = 600
    D1 = 200

    square_ops = SquareOperations()

    left_rect = box(start_x - 200, start_y - 1000, start_x, start_y + 1200)
    middle_rect = box(start_x, start_y, start_x + H1, start_y + D1)

    coordinate = [start_x + H1, start_y, start_y + D1]
    lw1 = [l1, w1]
    outer_square1, coordinateos_1, center1 = square_ops.plump(coordinate, lw1, True)

    rslw = [600, 200]
    rect_after_outer_square1, coordinaters_1 = square_ops.flows(coordinateos_1, rslw, False)

    lw2 = [l2, w2]
    outer_square2, coordinateos_2, center2 = square_ops.plump(coordinaters_1, lw2, False)

    rslw = [600, 200]
    rect_after_outer_square2, coordinaters_2 = square_ops.flows(coordinateos_2, rslw, True)

    lw3 = [l3, w3]
    outer_square3, coordinateos_3, center3 = square_ops.plump(coordinaters_2, lw3, lis[0])

    rslw = [600, 200]
    rect_after_outer_square3, coordinaters_3 = square_ops.flows(
        coordinateos_3, rslw, lis[1]
    )

    # lw4 = [l4, w4]
    # outer_square4, coordinateos_4, center4 = square_ops.plump(coordinaters_3, lw4, False)

    # rslw = [600, 200]
    # rect_after_outer_square4, _= square_ops.flows(coordinateos_4, rslw, True)

    # 合并所有外部形状
    merged_outer_shape = unary_union(
        [
            left_rect,
            middle_rect,
            outer_square1,
            rect_after_outer_square1,
            outer_square2,
            rect_after_outer_square2,
            outer_square3,
            rect_after_outer_square3,
            # outer_square4,
            # rect_after_outer_square4,
        ]
    )

    # 简化多边形以移除多余的点
    simplified_outer_shape = merged_outer_shape.simplify(0.001, preserve_topology=True)

    # 将外部形状转换为DXF中的多段线

    add_polygon_to_dxf(msp_outer, simplified_outer_shape)

    return doc_outer,[center1,center2,center3]
# 4


def doc_interbuild(center, shape_params):
    doc_inner = ezdxf.new(dxfversion="R2010")
    msp_inner = ShapeDrawer(doc_inner.modelspace())

    shape_sequence = list(shape_params.keys())

    for i, shape in enumerate(shape_sequence):
        shape_center = center[i]
        if "square" in shape_params[shape]:
            msp_inner.add_shape(
                "square", shape_center, shape_params[shape]["square"]["side_length"]
            )
        elif "circle" in shape_params[shape]:
            msp_inner.add_shape(
                "circle", shape_center, shape_params[shape]["circle"]["radius"]
            )
        elif "ellipse" in shape_params[shape]:
            msp_inner.add_shape(
                "ellipse",
                shape_center,
                # shape_params[shape]["ellipse"]["dimensions"],
                shape_params[shape]["ellipse"]["rotation"],
            )

    return doc_inner


def boolean_difference(doc_outer, doc_inner, result_filename):
    outer_polygons = [
        box(*entity.bbox()) for entity in doc_outer.modelspace().query("LWPOLYLINE")
    ]
    inner_polygons = [
        box(*entity.bbox()) for entity in doc_inner.modelspace().query("LWPOLYLINE")
    ]

    outer_union = unary_union(outer_polygons)
    inner_union = unary_union(inner_polygons)

    difference = outer_union.difference(inner_union)

    doc_result = ezdxf.new(dxfversion="R2010")
    msp_result = doc_result.modelspace()
    add_polygon_to_dxf(msp_result, difference)

    doc_result.saveas(result_filename)
