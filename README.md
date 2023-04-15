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


## Notes about internals
Core of the package is powered by SAT-solver, invoked in `solve` method of Formula class. Program searches for valid setup (setup is a partial mapping from package names to their available versions; setup is valid if all requirements for versioned packages in the setup are satisfied) by constructing a formula, where each versioned package corresponds to a single variable, such that formula is true if and only if setup is valid.

After that, to satisfy versioned package's dependencies, program finds a solution where variable of this version is True. In case of absence of such solutions, program doesn't take any steps to explain the result (although it can be extended to do this by considering formulas with additional requirements, e.g. checking whether direct requirements can be satisfied by adding a single clause to the CNF of the formula).

As mentioned earlier, program can handle dependencies specified not only by ranges, but by any sets of versions (via `--mode` flag; internally they are represented as a union of ordered ranges, see `VersionRange` class in `resolver/parser.py`). It is possible to adapt this package to handle any types of linearly-ordered versions (e.g. SemVer, by changing `Version.version` type) and open ranges of versions.

To run tests, run `scripts/run_tests.sh` with path to packageIndex.txt. To see the results of satisfy for all versions of all packages, run `scripts/batch_satisfy.sh`. Examples of invocation of both scripts are described in the next section.

### Project structure
```
├── README.md      
├── requirements.txt
├── resolver               # package itself
│   ├── __init__.py        
│   ├── __main__.py          
│   ├── parser.py          # Used classes (Version, VersionedPackage, etc), parser functions
│   └── utils.py           # CLI handlers, solver for satisfier (see class Formula)
├── scripts
│   ├── batch_satisfy.sh   # Run to see results of `satisfy` for all packages 
│   │                      # Arguments are path to index, mode and output file (optional)
│   │                      # $ ./scripts/batch_satisfy packageIndex.txt intersection /dev/stdout
│   ├── run_tests.sh       # Run tests (both python & shell scripts)
│   │                      # $ ./scripts/run_tests.sh path/to/packageIndex.txt
│   └── test_cli.sh        # Test `latest` subcommand;    
│                          # $ ./scripts/test_cli.sh path/to/packageIndex.txt
├── test_data              # not used
│   └── two_packages.txt
└── tests                  # tests package. Run by `$ python3 -m tests`
    ├── __init__.py
    ├── __main__.py
    ├── test_parser.py
    └── tests.py
```
