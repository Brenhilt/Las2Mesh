# Python3, vim: set fileencoding=utf-8:
# Author  : Ryosuke Munekata <m@xmo.jp>
# Created : 2023/09/14


# {{{ modules loading
from argparse import ArgumentParser
from os import remove
from os.path import splitext

from laspy import read as read_las
from numpy import amax, amin, array, empty, full, vstack
from numpy import column_stack as cstack
from open3d.io import write_triangle_mesh
from open3d.geometry import (
    KDTreeSearchParamKNN,
    PointCloud,
    TriangleMesh
)
from open3d.utility import (
    Vector3dVector,
    VerbosityContextManager,
    VerbosityLevel
)
from open3d.visualization import draw_geometries
from pygltflib.utils import gltf2glb
# }}}


# {{{ const settings
WRITE_OPT = dict(
    write_ascii=False,
    write_vertex_normals=True
)
# }}}


# Display Help if no option
class ArgumentParserDH(ArgumentParser):
    def error(self, message):
        self.print_help()
        exit()


def draw_geodata(datas, window_name):
    # from open3d.visualization import draw,
    # draw(mesh) # 詳細設定用
    # 画面表示
    draw_geometries([datas], window_name=window_name)
    # 操作方法
    # http://www.open3d.org/docs/latest/tutorial/Basic/visualization.html
    return None


# lasファイルから点群を追加する
def add_points(filename, points, colors):
    las = read_las(filename)
    scales = las.header.scales
    pe2 = [las.points.X * scales[0],
           las.points.Y * scales[1],
           las.points.Z * scales[2]]
    points = vstack([points, cstack(pe2)])
    if hasattr(las.points, 'red'):
        # カラーあり
        ce2 = [las.points.red,
               las.points.green,
               las.points.blue]
        colors = vstack([colors, cstack(ce2) / 65535.])
    else:
        # カラーなし(グレー表示)
        ge2 = [full((len(las.X), 3), 0.5)]
        colors = vstack([colors, cstack(ge2)])
    return points, colors


# 点群からメッシュを生成
def create_mesh(points, depth):
    # 法線の推定
    points.estimate_normals(search_param=KDTreeSearchParamKNN(knn=20))

    # Upの軸を指定する
    points.orient_normals_to_align_with_direction(
        orientation_reference=array([0., 0., 1.])
    )

    # メッシュ化
    with VerbosityContextManager(VerbosityLevel.Debug):
        poisson, dens = TriangleMesh.create_from_point_cloud_poisson(
            points, depth=depth)
    print(poisson)

    box = points.get_axis_aligned_bounding_box()
    mesh = poisson.crop(box)

    # メッシュの軽量化
    # decimation_ratio = 0.5
    # count = len(mesh.triangles)
    # mesh = mesh.simplify_quadric_decimation(int(count * decimation_ratio))
    return mesh


def write_mesh(dst, mesh, override=True, write_opt=WRITE_OPT):
    path, ext = splitext(dst)
    if ext == ".glb":
        gltf = f"{path}.gltf"
        write_triangle_mesh(gltf, mesh, **write_opt)
        gltf2glb(gltf, override=override)
        remove(gltf)
    else:
        write_triangle_mesh(dst, mesh, **write_opt)


# 複数の .lasファイルを読み込み1つの点群にする
def load_files(files):
    vec = empty((0, 3))
    col = empty((0, 3))

    for filename in files:
        vec, col = add_points(filename, vec, col)
        print(f"{filename} => {len(vec)} points(total)")

    # 端が原点となるように移動
    p_min = amin(vec, axis=0)
    p_max = amax(vec, axis=0)
    vec = vec - p_min
    box = p_max - p_min
    print(f"size: {box[0]:.1f} x {box[1]:.1f} x {box[2]:.1f} (m)")
    pcd = PointCloud()
    pcd.points = Vector3dVector(vec)
    pcd.colors = Vector3dVector(col)
    return pcd
