# Contributing

Keep the report's metric grains explicit. A change to note matching, searched fields, description normalization, or row identity changes the analytical contract and requires documentation and tests.

Use synthetic data in examples, tests, issues, and pull requests. Never paste company catalog extracts, licensed reference content, private server names, or credentials.

Run the dependency-free demo, unit tests, generated-artifact check, and `git diff --check` before proposing changes. State separately whether you ran the optional SQL Server integration checker and identify the engine version when you did.

The public edition does not modify production data. Do not add write-back behavior, automatic qualifier selection, or standards-validation claims without an explicit reviewed design and supporting tests.

No contribution license or redistribution license has been selected. Resolve ownership and licensing before accepting external code for a public release.
