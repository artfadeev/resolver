from resolver.parser import (
    VersionedPackage,
    Version,
    VersionRange,
    parse_entry,
    VersionSet,
)


def test_types():
    v1 = Version(1)
    v2 = Version(2)
    v50 = Version(50)
    v100 = Version(100)
    v150 = Version(150)
    v200 = Version(200)

    r1_2 = VersionRange(v1, v2)
    r100_200 = VersionRange(v100, v200)

    s = VersionSet([r1_2, r100_200])

    assert v1 < v2 <= v50
    assert v1 != v2 == v2

    assert v150 in r100_200
    assert v50 not in r1_2

    assert v150 in s
    assert v50 not in s
    assert v100 in s

    assert max([v1, v2, v100, v150]) == v150
    assert min([v1, v2, v150]) == v1

    print("test_types success!")


def test_parser():
    tests = {
        " requests 123:  beautifulsoup 1..10  , multiset 12\n": (
            VersionedPackage("requests", Version(123)),
            [
                ("beautifulsoup", VersionRange(Version(1), Version(10))),
                ("multiset", VersionRange(Version(12), Version(12))),
            ],
        ),
        "without_dependencies 123:": (
            VersionedPackage("without_dependencies", Version(123)),
            [],
        ),
    }

    for test, expected_result in tests.items():
        assert parse_entry(test) == expected_result

    print("test_parser success!")


if __name__ == "__main__":
    test_types()
    test_parser()
