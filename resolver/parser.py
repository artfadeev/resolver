from dataclasses import dataclass
from collections import defaultdict

# PART 1: abstraction definitions


@dataclass(frozen=True)
class Version:
    """Representation of version of a package

    Supports only single-number version"""

    v: int

    def __lt__(self, other):
        return self.v < other.v

    def __le__(self, other):
        return self.v <= other.v

    def __eq__(self, other):
        return self.v == other.v

    def __str__(self):
        return str(self.v)


@dataclass
class VersionRange:
    """Closed range of versions"""

    start: Version
    end: Version

    def __str__(self):
        if self.start == self.end:
            return f"{self.start.v}"
        return f"{self.start.v}..{self.end.v}"

    def __contains__(self, item: Version):
        return self.start <= item <= self.end


class VersionSet:
    """Set of versions"""

    def __init__(self, ranges=None):
        if ranges is None:
            ranges = []
        self.ranges = ranges

    def add_range(self, r: VersionRange):
        self.ranges.append(r)

    def __contains__(self, item: Version):
        for r in self.ranges:
            if item in r:
                return True
        return False

    def __repr__(self):
        return f"VersionSet({self.ranges})"


@dataclass(frozen=True)  # frozen=True makes objects hashable
class VersionedPackage:
    name: str
    version: Version


# PART 2: package index supporting functions (nothing more than parsing)


def parse_version(s):
    """Parse version string

    Syntax:
        '<n>' where n is version number (integer)
    """
    return Version(int(s))


def parse_range(s):
    """Parse string denoting range of versions

    Syntax:
        '<n>' for a range consisting of a single version
        '<m>..<n>' for a range consisting of versions m<=k<=n
    """
    if ".." in s:
        start_, end_ = s.split("..")
        return VersionRange(parse_version(start_), parse_version(end_))
    else:
        v = parse_version(s)
        return VersionRange(v, v)


def parse_package_version(s):
    """Parse string denoting versioned package

    Syntax:
        '<package_name> <version>'
    """
    name, version = s.strip().split()
    return VersionedPackage(name, parse_version(version))


def parse_dependency(s):
    """Parse single dependency

    Syntax:
        '<package_name> <version_range>'
    """
    name, range_ = s.split()
    return name, parse_range(range_)


def parse_dependencies(s):
    """Parse list of dependencies

    Syntax:
        '<dependency>, ..., <dependency>'
    """
    deps = s.strip().split(",")
    if deps == [""]:  # no dependencies
        return []

    return [parse_dependency(dep.strip()) for dep in deps]


def parse_entry(entry):
    """Parse package index entry

    Syntax:
        '<package_name> <version>: <dependency>, ..., <dependency>'
    """
    package, dependencies = entry.strip().split(":")

    return parse_package_version(package), parse_dependencies(dependencies)


# PART 3: actual logic of parser
def load_package_index(path):
    """Load package index from disk

    Returns
        index -- nested dictionary.
            First level:  key is package name PACKAGE, value is dictionary indexed by versions
            Second level: key is version VERSION, value is dictionary indexed by package names
            Third level:  key is package name DEP, value is VersionSet of versions, which
                suit dependency DEP for version VERSION of package PACKAGE
    """
    index = defaultdict(lambda: defaultdict(lambda: defaultdict(VersionSet)))
    with open(path, "r") as file:
        for line in file:
            pv, deps = parse_entry(line)
            for dep, rang in deps:
                index[pv.name][pv.version][dep].add_range(rang)
    return index
