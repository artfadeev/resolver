from .parser import load_package_index
from .utils import latest_version, satisfy

from argparse import ArgumentParser


def show_latest_version(index, package: str):
    if package not in index.keys():
        print(f"There is no package named '{package}'")
        # TODO: suggest name of lexicographically nearest package
        return

    v = latest_version(index, package)
    print(v)


def main():
    parser = ArgumentParser(prog="resolver")
    subparsers = parser.add_subparsers(dest="subcommand")

    # TODO: path to the index of packages may be stored in environmental variable
    parser.add_argument(
        "-I",
        "--index",
        dest="path",
        required=True,
        help="path to package index",
    )
    parser.add_argument(
        "--mode",
        dest="mode",
        default="intersection",
        help='mode of handling multiple dependencies of a versioned package on a single package. Can be either "intersection" or "union".',
    )

    subcommand_latest = subparsers.add_parser(
        "latest", help="show latest version of package"
    )
    subcommand_latest.add_argument("package", help="package name")

    subcommand_satisfy = subparsers.add_parser(
        "satisfy", help="satisfy dependencies of requested package"
    )
    subcommand_satisfy.add_argument("package", help="package name")
    subcommand_satisfy.add_argument("version", help="package version")
    subcommand_satisfy.add_argument(
        "--oneline",
        dest="oneline",
        action="store_true",
        help="print result as single line of comma-delimited list of versioned packages",
    )

    args = parser.parse_args()
    if args.subcommand is None:
        parser.print_help()
        exit()

    index, dependencies = load_package_index(args.path, mode=args.mode)
    if args.subcommand == "latest":
        show_latest_version(index, args.package)
    elif args.subcommand == "satisfy":
        satisfy(
            index,
            dependencies,
            args.package,
            args.version,
            oneline=args.oneline,
        )


if __name__ == "__main__":
    main()
