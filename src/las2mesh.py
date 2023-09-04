from argparse import ArgumentParser
import os

import laspy
from numpy import amax, amin, array, empty, full
from numpy import vstack
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


VERSION = "Las2Mesh v0.3b"


# lasファイルから点群を追加する
def add_points(filename, points, colors):
    las = laspy.read(filename)
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


# 複数の .lasファイルを読み込み1つの点群にする
def load_files(files):
    vec = empty((0, 3))
    col = empty((0, 3))

    for filename in files:
        vec, col = add_points(filename, vec, col)
        print(f"{filename} => {len(vec)} points(total)")

    # 端が原点となるように移動
    min = amin(vec, axis=0)
    max = amax(vec, axis=0)
    vec = vec - min
    bbox = max - min
    print(f"size: {bbox[0]:.1f} x {bbox[1]:.1f} x {bbox[2]:.1f} (m)")
    pcd = PointCloud()
    pcd.points = Vector3dVector(vec)
    pcd.colors = Vector3dVector(col)
    return pcd


# 点群からメッシュを生成
def create_mesh(point_cloud, mesh_depth):
    # 法線の推定
    point_cloud.estimate_normals(search_param=KDTreeSearchParamKNN(knn=20))

    # Upの軸を指定する
    point_cloud.orient_normals_to_align_with_direction(
        orientation_reference=array([0., 0., 1.])
    )

    # メッシュ化
    with VerbosityContextManager(VerbosityLevel.Debug):
        poisson_mesh, densities = TriangleMesh.create_from_point_cloud_poisson(
            point_cloud, depth=mesh_depth)
    print(poisson_mesh)

    bbox = point_cloud.get_axis_aligned_bounding_box()
    mesh = poisson_mesh.crop(bbox)

    # メッシュの軽量化
    # decimation_ratio = 0.5
    # count = len(mesh.triangles)
    # mesh = mesh.simplify_quadric_decimation(int(count * decimation_ratio))
    return mesh


def write_mesh(filename, mesh):
    opt = dict(write_ascii=False, write_vertex_normals=True)
    body, ext = os.path.splitext(filename)
    if ext == ".glb":
        gltf_file = body + ".gltf"
        write_triangle_mesh(gltf_file, mesh, **opt)
        gltf2glb(gltf_file, override=True)
        os.remove(gltf_file)
    else:
        write_triangle_mesh(filename, mesh, **opt)


def main():
    print(VERSION)
    parser = ArgumentParser(description=".lasファイルからメッシュを生成します")
    parser.add_argument('files', nargs='*',
                        help="対象の .lasファイル。複数指定できます。")
    parser.add_argument('-d', '--depth', default=10, type=int,
                        help=("メッシュの細かさを整数で指定します。"
                              "デフォルト値は 10 です。"))
    parser.add_argument('-o', '--output', default='output.ply',
                        help=("出力ファイル名を指定します。"
                              "デフォルト値は output.ply です。出力形式は、"
                              ".ply, .stl, .obj, .off, .gltf"
                              " に対応しています。"))
    parser.add_argument('-n', '--nopreview', action='store_true',
                        help="3Dプレビュー表示を無効にします")
    args = parser.parse_args()

    if len(args.files) == 0:
        parser.print_help()
        return

    pcd = load_files(args.files)
    output_path = args.output
    depth = args.depth

    mesh = create_mesh(pcd, depth)
    write_mesh(output_path, mesh)

    if not args.nopreview:
        # from open3d.visualization import draw,
        # draw(mesh) # 詳細設定用
        # 画面表示
        wname = f"{VERSION} - {output_path} (preview)"
        draw_geometries([mesh], window_name=wname)
        # 操作方法:
        # http://www.open3d.org/docs/latest/tutorial/Basic/visualization.html


if __name__ == '__main__':
    main()
