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
    r2_50 = VersionRange(v2, v50)
    r100_200 = VersionRange(v100, v200)

    try:
        VersionRange(Version(100), Version(50))
    except Exception:
        pass
    else:
        raise Exception("Invalid VersionRange passes test")

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

    assert r1_2.union(r2_50) == VersionRange(v1, v50)
    try:
        r1_2.union(r100_200)
    except Exception as e:
        pass
    else:
        raise Exception("Union of two disjunct ranges should produce an error!")

    assert set(s.pick([v100, v2, v50, v150, v200])) == {v2, v100, v150, v200}

    print("test_types success!")


def test_VersionSet():
    vs = VersionSet

    def vr(v1, v2):
        return VersionRange(Version(v1), Version(v2))

    # test __init__
    vs1 = vs([vr(110, 120), vr(250, 300), vr(1, 100), vr(50, 200)])
    vs2 = vs([vr(1, 200), vr(250, 300)])
    assert vs1.ranges == vs2.ranges

    # test union and intersection
    vs3 = vs([vr(100, 220), vr(260, 270), vr(280, 290), vr(300, 3000)])
    assert vs3.intersection(vs1).ranges == vs1.intersection(vs3).ranges
    assert vs3.union(vs1).ranges == vs1.union(vs3).ranges

    assert vs3.intersection(vs1).ranges == [
        vr(100, 200),
        vr(260, 270),
        vr(280, 290),
        vr(300, 300),
    ]
    assert vs3.union(vs1).ranges == [vr(1, 220), vr(250, 3000)]

    print("test_VersionSet success!")


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
    test_VersionSet()
    test_parser()
