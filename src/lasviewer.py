from .common import ArgumentParserDH, load_files, draw_geodata


VERSION = "LasViewer v1.0 based on Las2Mesh"


def option_parse():
    parser = ArgumentParserDH(description=".lasファイルを表示します")
    parser.add_argument('files', nargs="+",
                        help='対象の .lasファイル。複数指定できます。')
    options = parser.parse_args()
    return options


def main():
    print(VERSION)
    options = option_parse()
    pcd = load_files(options.files)
    draw_geodata([pcd], VERSION)


if __name__ == '__main__':
    main()
