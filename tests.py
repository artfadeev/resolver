from resolver.parser import (
    VersionedPackage,
    load_package_index,
    VersionSet,
    VersionRange,
    Version,
)
from resolver.utils import Formula, Solver, reduce_setup
from sys import argv

INDEX_PATH = argv[1] if len(argv) >= 2 else "./packageIndex.txt"


def v(n):
    return Version(n)


def vr(a, b):
    return VersionRange(Version(a), Version(b))


def vs(*args):
    return VersionSet(list(args))


def vp(name, v):
    return VersionedPackage(name, Version(v))


INDEX_TEST_CASE = {
    "a": {v(1), v(2), v(3)},
    "b": {v(1), v(2)},
    "c": {v(1), v(3)},
}

DEPS_TEST_CASE = {
    vp("a", 1): {},  # satisfiable
    vp("a", 2): {"b": vs(vr(1, 1))},  # unsatisfiable
    vp("a", 3): {"b": vs(vr(1, 1), vr(3, 3))},  # unsatisfiable
    vp("b", 1): {"c": vs(vr(1, 1))},  # unsatisfiable
    vp("b", 2): {"c": vs(vr(1, 3))},  # satisfiable
    vp("c", 1): {"d": vs()},  # unsatisfiable: impossible dep
    vp("c", 3): {},  # satisfiable
}

SATISFIABLE = {vp("a", 1), vp("b", 2), vp("c", 3)}


def check_setup(dependencies, setup):
    for package in setup:
        v = setup[package]
        pv = VersionedPackage(package, v)

        for dep, vs in dependencies[pv].items():
            assert setup[dep] in vs


def test_check_setup():
    deps = DEPS_TEST_CASE

    check_setup(deps, {})
    check_setup(deps, {"c": v(3)})
    check_setup(deps, {"b": v(2), "c": v(3)})
    try:
        check_setup(deps, {"a": v(3), "b": v(1), "c": v(3)})
    except Exception:
        pass
    else:
        raise Exception("check_setup failed on invalid setup")

    print("test_check_setup passed tests!")


def test_Formula():
    f = Formula.from_dependencies(INDEX_TEST_CASE, DEPS_TEST_CASE)

    solver = Solver(bootstrap_with=f.formula)
    satisfiable = set(
        filter(lambda var: solver.solve(assumptions=[var]), range(1, 8))
    )
    assert satisfiable == set(map(f.vp_to_var.__getitem__, SATISFIABLE))

    print("test_Formula passed tests!")


def test_reduce_setup():
    f = Formula.from_dependencies(INDEX_TEST_CASE, DEPS_TEST_CASE)

    test_cases = [
        (vp("a", 1), {"a": v(1)}),
        (vp("b", 2), {"b": v(2), "c": v(3)}),
        (vp("c", 3), {"c": v(3)}),
    ]
    for vp_, minimal_setup in test_cases:
        is_sat, setup = f.solve(assumptions=[vp_])
        assert is_sat
        assert reduce_setup(DEPS_TEST_CASE, setup, [vp_.name]) == minimal_setup

    print("test_reduce_setup passed tests!")


if __name__ == "__main__":
    test_check_setup()
    test_Formula()
    test_reduce_setup()
