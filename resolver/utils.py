from itertools import combinations
from collections.abc import Iterable
from collections import deque

from pysat.formula import CNF
from pysat.solvers import Solver

from .parser import parse_version, Version, VersionedPackage


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
