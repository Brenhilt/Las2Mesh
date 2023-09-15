from common import (
    ArgumentParserDH, load_files, preview,
    create_mesh, write_mesh,
)


VERSION = "Las2Mesh v0.3b"


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
    parser.add_argument('-n', '--nopreview', action="store_true",
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
        window_name = f"{VERSION} - {output} (preview)"
        preview(mesh, window_name)


if __name__ == '__main__':
    main()
