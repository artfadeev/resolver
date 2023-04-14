# Package resolver
This repository contains package resolver written as a test task for internship. It doesn't suit any practical needs.

## Usage
To use the resolver, you need an index file — it specifies available packages and their dependencies. Index file consists of a list of entries, where eachy entry specifies list of dependencies of some versioned package. Dependencies are specified by name of a required package followed by range of possible versions (either `a..b` for closed range from a to b, or `a` for just one version). If for some versioned package there are multiple dependencies on some other package, the intersection of provided ranges is taken (you can change this behaviour to uniting the ranges instead by providing `--mode union` option). Path to the index file must be provided by `--index`/`-i` option.

I suggest setting up a shell alias:
```bash
alias resolver="python3 -m resolver --index path/to/packageIndex.txt"
```

### Subcommand `latest`
`resolver latest` followed by a package name provides latest version of this package available in the package index:

```bash
$ resolver latest reeler
12
```

### Subcommand `satisfy`
This subcommand satisfied a setup of packages such that particular versioned package is present:
```bash
$ resolver satisfy dissevered 0
This package can be satisfied with following packages:
dissevered 0 with following dependencies:
  prerestrict 0 with following dependencies:
    predenying 0 with following dependencies:
      pokes 0
    pokes 0 (see above)
  congruous 0 with following dependencies:
    predenying 0 (see above)
    pokes 0 (see above)

$ resolver satisfy dissevered 0 --oneline
congruous 0, prerestrict 0, pokes 0, predenying 0, dissevered 0
```





## Installation
The only dependency out of standard library is `python-sat`. `requirements.txt` is provided, so all you need is to run
`python3 -m pip install -r requirements.txt`
