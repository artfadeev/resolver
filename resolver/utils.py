class UnknownPackageError(Exception):
    pass


def latest_version(index, package: str):
    if package not in index.keys():
        raise UnknownPackageError
    return max(index[package])
