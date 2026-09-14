# Publishing the Portfolio Repository

## Current State

The GitHub destination is [Kuvelet/qdb-mapping-impact](https://github.com/Kuvelet/qdb-mapping-impact), created as a private repository for review. The release contains the reviewed portfolio package, not the parent working directory or private source data. Publishing the code does not publish a website or grant an open-source license.

The initial GitHub release is a snapshot uploaded through the connected GitHub integration. The original local development history is retained separately; it is not a Git push of that history. For subsequent Git-based work, clone the GitHub repository with an authenticated client so new commits share its history. Do not force-push the separate local build history over the remote.

Repository name: `qdb-mapping-impact`.

Suggested description: `Python Qdb mapping automation with SQL analysis of low-confidence notes, mapping progress, and catalog impact. Includes a business case, SQL report, and synthetic demo.`

Suggested topics: `python`, `selenium`, `automation`, `sql-server`, `tsql`, `data-quality`, `automotive-aftermarket`, `catalog-management`, `data-analytics`, `aces`, `qdb`, `portfolio`.

## Before the First Push

- Confirm that the intended employer attribution and aggregate results may be publicly shared. The project owner confirmed both for this draft.
- Separately confirm permission to publish the adapted code and select a license if appropriate. Company-data permission is not automatically code-licensing permission.
- Confirm the desired author name and public-safe Git email. The connected account identifies Can Kuvelet (`Kuvelet`); local commits use a GitHub no-reply email rather than the account's personal email.
- Review all tracked files, including fixtures, charts, history, and source templates. `.gitignore` is not a security boundary.
- Keep real catalog exports, mapping sheets, licensed reference data, screenshots of internal systems, connection strings, and production adapters out of Git.
- Run the tests and demo, inspect the chart, and resolve broken links.
- Keep reported company results labeled as reported; do not relabel synthetic fixtures as a reproduction of the full project.
- Keep source-derived PIM workflows, portfolio execution controls, and the synthetic reference model distinguishable. The three automation scripts are now included; their live PIM behavior and dependency combinations still require authorized validation.
- Review the documented Remove Mapping behavior, input privacy, and CSV outcome semantics. Do not describe a submitted Save as a verified production correction.

Start private when ownership or release review is incomplete. Public visibility can be enabled after review. Do not upload the parent working directory: it contains the original company-specific query and email draft outside this repository.

## Suggested GitHub Presentation

Pin the repository to your profile. The README provides a short business narrative, approved scale metrics, and a runnable example before linking to detailed technical material. No badge claims a CI run before one actually succeeds.

For the personal portfolio page, use the short card and case-study narrative in `docs/portfolio.md`, together with `assets/project-impact.png`. The chart is not evidence of reduced returns or higher sales, and it should retain its scope caption.

Keep the full technical documents in GitHub rather than making the portfolio page too dense. Link directly to the README, Python automation guide, SQL file, metric example, and test suite.

## Release Checklist

```bash
python tools/build_demo.py --check
python -m unittest discover -s tests -v
python -m qdb_impact
git diff --check
git status --short
```

The optional chart builder uses Pillow:

```bash
python tools/build_chart.py
```

For a target SQL Server, run the optional full-engine checker and record the engine version and result. Synthetic CI is useful but should not be described as SQL Server integration verification.

## Future Updates

Replace the approved aggregate evidence file only with a new approved snapshot. Add an actual source snapshot date once known. Regenerate the chart and revise the prose when metrics change; numbers embedded in case-study copy are not rewritten automatically.

If the report's column set, matching normalization, source-view definition, or note-list scope changes, document the change because trend comparisons may no longer be like-for-like.
