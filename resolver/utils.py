from itertools import combinations
from collections.abc import Iterable
from collections import deque

from pysat.formula import CNF
from pysat.solvers import Solver

from .parser import parse_version, Version, VersionedPackage, VersionSet


class UnknownPackageError(Exception):
    pass


# raised when presumably valid setup has unsatisfied dependency
class UnsatisfiedDependencyError(Exception):
    pass


# raised when presumably valid setup has several versions of the same package
class MultipleVersionsError(Exception):
    pass


def latest_version(index, package: str):
    if package not in index.keys():
        raise UnknownPackageError
    return max(index[package])


class Formula:
    """Wrapper around pysat.formula with better interface"""

    def __init__(self, formula: CNF, bijection: dict[VersionedPackage, int]):
        self.formula = formula
        self.vp_to_var = bijection
        self.var_to_vp = dict(map(reversed, bijection.items()))

    def _name(self, vars):
        """Decode VersionedPackages from corresponding variable numbers"""
        return list(map(self.var_to_vp.__getitem__, vars))

    def solve(self, assumptions: list[VersionedPackage] | None = None):
        """Find solution to the formula where variables for `assumptions` are true

        Note that returned setup is not guaranteed to be minimal. Use reduce_setup
        if you want to reduce it.

        Returns: (is_satisfiable, setup)
            is_satisfiable (bool)
            setup (dict[str, Version]|None): setup or None if is_satisfiable==False
        """
        if assumptions is None:
            assumptions = []
        assumptions_vars = list(map(self.vp_to_var.__getitem__, assumptions))

        with Solver(bootstrap_with=self.formula) as solver:
            if not solver.solve(assumptions=assumptions_vars):
                return False, None
            vps = [self.var_to_vp[v] for v in solver.get_model() if v > 0]

        setup = {vp.name: vp.version for vp in vps}
        return True, setup

    def any_satisfiable(self, packages: Iterable[VersionedPackage]):
        """Test whether at least one from packages can be satisfied"""
        new_formula = self.formula.clauses + [
            self.vp_to_var[vp] for vp in packages
        ]
        with Solver(bootstrap_with=new_formula) as solver:
            return solver.solve()

    @classmethod
    def from_dependencies(cls, index, dependencies):
        """Create formula characterizing valid setups

        Returns:
            formula (Formula)
        """

        # There is a bijection between VersionedPackages and variables.
        # Set of variables with value 1 will correspond to VersionedPackages
        # in the setup.
        bijection = dict(map(reversed, enumerate(dependencies.keys(), start=1)))

        clauses = []
        # Add clauses which prohibit several versions of the sae package
        for package in index.keys():
            vars = map(
                lambda v: bijection[VersionedPackage(package, v)],
                index[package],
            )
            for v1, v2 in combinations(vars, 2):
                clauses.append([-v1, -v2])

        # Add clauses which check that dependencies are satisfied
        for vp, deps in dependencies.items():
            for requirement, vs in deps.items():
                possible_versions = vs.pick(index.get(requirement, {}))

                # Either one of `possible_versions` is present in the setup,
                clause = [
                    bijection[VersionedPackage(requirement, v)]
                    for v in possible_versions
                ]
                # ... or `vp` is absent
                clause.append(-bijection[vp])
                clauses.append(clause)

        formula = CNF(from_clauses=clauses)
        return cls(formula, bijection)


def reduce_setup(dependencies, setup: dict[str, Version], keep: Iterable[str]):
    """Reduce setup by removing everything except `keep` and its dependencies

    Arguments:
        dependencies (dict[VersionedPackage, dict[str, VersionSet]])
        setup (dict[str, Version]): setup to be reduced
        keep (Iterable[str]): package names to be kept

    Returns:
        new_setup (dict[str, Version])
    """
    if not set(keep).issubset(setup.keys()):
        raise Exception("All packages from `keep` should be in the setup!")

    new_setup_packages = set(keep)
    queue = deque(keep)

    while queue:
        package = queue.popleft()
        version = setup[package]
        for requirement in dependencies[VersionedPackage(package, version)]:
            if requirement not in new_setup_packages:
                new_setup_packages.add(requirement)
                queue.append(requirement)
    return {package: setup[package] for package in new_setup_packages}


def is_versionset_satisfiable(
    index, formula: Formula, package: str, vs: VersionSet
):
    """Check if there is solution of formula where `package` has version from vs"""
    versions = vs.pick(index[package])
    vps = [VersionedPackage(package, v) for v in versions]

    return formula.any_satisfiable(vps)


def satisfy(index, dependencies, package: str, version: str, oneline=False):
    version = Version(int(version))
    if package not in index:
        raise UnknownPackageError(f"There is no package named {package}")
    if version not in index[package]:
        raise UnknownVersionError(
            f"There is no version {str(version)} of {package}"
        )
    vp = VersionedPackage(package, version)

    formula = Formula.from_dependencies(index, dependencies)

    is_satisfiable, setup = formula.solve(assumptions=[vp])
    if not is_satisfiable:
        print("This package version can't be satisfied")

        """
        # We'll try to explain why:
        # Check if for some dependency, none of versions in the
        # corresponding versionset is satisfiable
        for dep, vs in dependencies[vp].items():
            if not is_versionset_satisfiable(index, formula, dep, vs):
                print(f"None of versions {str(vs)} of dependency package {dep} is satisfiable!")
        """
        return

    if oneline:
        setup = reduce_setup(dependencies, setup, [vp.name])
        print(", ".join(f"{name} {v}" for name, v in setup.items()))
    else:
        print("This package can be satisfied with following packages:")
        print_transitive_dependencies(index, dependencies, setup, package)


def print_transitive_dependencies(
    index, dependencies, setup: dict[str, Version], root_package: str
):
    """Pretty-print to stdout root_package and all of its dependencies"""
    printed = set()

    def pp(package: str, level: int, prefix="  "):
        vp = VersionedPackage(package, setup[package])
        # dependencies do not necessarily form a tree, so cycles and
        # repeated subtrees should be prevented from printing
        if package in printed:
            print(f"{prefix*level}{package} {vp.version} (see above)")
            return

        printed.add(package)

        has_subdependencies = (
            " with following dependencies:" if dependencies[vp] else ""
        )

        print(f"{prefix*level}{package} {vp.version}{has_subdependencies}")
        for dep in dependencies[vp]:
            pp(dep, level + 1, prefix)

    pp(root_package, 0)
