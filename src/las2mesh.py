from argparse import ArgumentParser
from os import remove
from os.path import splitext

from laspy import read as read_las
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
WRITE_OPT = dict(
    write_ascii=False,
    write_vertex_normals=True
)


# display help if no option
class ArgumentParserDH(ArgumentParser):
    def error(self, message):
        self.print_help()
        exit()


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


def option_parse():
    parser = ArgumentParserDH(description=".lasファイルからメッシュを生成します")
    parser.add_argument('files', nargs="+",
                        help="対象の .lasファイル。複数指定できます。")
    parser.add_argument('-d', '--depth', default=10, type=int,
                        help=("メッシュの細かさを整数で指定します。"
                              "デフォルト値は 10 です。"))
    parser.add_argument('-o', '--output', default='output.ply',
                        help=("出力ファイル名を指定します。"
                              "デフォルト値は output.ply です。"
                              "出力形式は、.ply, .stl, .obj, .off, .gltf に対応しています。"))
    parser.add_argument('-n', '--nopreview', action='store_true',
                        help="3Dプレビュー表示を無効にします")
    options = parser.parse_args()
    return options


def main():
    print(VERSION)
    options = option_parse()

    pcd = load_files(options.files)
    output = options.output
    depth = options.depth

    mesh = create_mesh(pcd, depth)
    write_mesh(output, mesh)

    if not options.nopreview:
        # from open3d.visualization import draw,
        # draw(mesh) # 詳細設定用
        # 画面表示
        draw_geometries([mesh], window_name=f"{VERSION} - {output} (preview)")
        # 操作方法:
        # http://www.open3d.org/docs/latest/tutorial/Basic/visualization.html


if __name__ == '__main__':
    main()
