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


@dataclass(frozen=True)
class VersionRange:
    """Closed non-empty range of versions"""

    start: Version
    end: Version

    def __post_init__(self):
        if self.end < self.start:
            raise Exception(
                "End version of VersionRange should be no less than start version"
            )

    def union(self, other):
        """Returns union of two intersecting ranges"""
        if self.end < other.start or other.end < self.start:
            raise Exception  # TODO: specify

        return VersionRange(min(self.start, other.start), max(self.end, other.end))

    def __str__(self):
        if self.start == self.end:
            return f"{self.start.v}"
        return f"{self.start.v}..{self.end.v}"

    def __contains__(self, item: Version):
        return self.start <= item <= self.end


class VersionSet:
    """Set of versions

    VersionSet is stored as an ordered sequence of disjunct version ranges (see VersionRange)
    """

    # TODO: make ranges sorted and disjunct

    def __init__(self, ranges: list[VersionRange] = None):
        if ranges is None:
            ranges = []

        self.ranges = []

        if not ranges:
            return

        ranges.sort(key=lambda r: r.start)
        current = ranges[0]
        for r in ranges:
            if current.end < r.start:
                self.ranges.append(
                    current
                )  # note that VersionRange is frozen dataclass
                current = r
            else:
                current = current.union(r)
        self.ranges.append(current)

    def add_range(self, r: VersionRange):
        self.ranges.append(r)

    def union(self, other):
        # TODO: can be done in linear time, but this is quick enough
        # TODO: don't forget about this method when implementing unclosed VersionRange
        return VersionSet(self.ranges + other.ranges)

    def intersection(self, other):
        ranges = []
        i, j = 0, 0
        while i < len(self.ranges) and j < len(other.ranges):
            left = self.ranges[i]
            right = other.ranges[j]

            if left.end < right.start:
                i += 1
                continue
            if right.end < left.start:
                j += 1
                continue

            # now we know that two ranges intersect
            if left.end < right.end:
                ranges.append(VersionRange(max(left.start, right.start), left.end))
                i += 1
            else:
                ranges.append(VersionRange(max(left.start, right.start), right.end))
                j += 1
        return VersionSet(ranges)

    def pick(self, versions):  # TODO: add typehint iterable
        """Pick versions from iterable present in this VersionSet

        Returns:
            result (iterable)
        """

        return set(filter(self.__contains__, versions))

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
