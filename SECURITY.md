# Data and Security

Do not commit credentials, source exports, employer documents, or licensed reference data. Use private input adapters and authorized database identities with the least permissions needed. The synthetic demo requires no permanent-table writes. The separate Python automation defaults to local preview, but an explicitly enabled live run removes existing PIM mappings before adding replacements. Review the [execution controls and recovery boundaries](docs/python-automation.md) before using it.

Do not include sensitive examples in public issue reports. Report a sensitive-data exposure privately to the repository owner through an available private channel; no contact address has been invented for this draft.

If a secret is accidentally published, revoke or rotate it immediately and follow the organization's incident process. Adding a file to `.gitignore` does not remove it from Git history.

Live execution logs and batch CSVs contain input note/qualifier text and may contain licensed or confidential data. Keep them in approved private storage, inspect exception content before sharing it, and avoid automatic formula evaluation when opening CSVs in spreadsheet software. A custom output directory does not make its contents publishable.

The static repository checks look for several known leakage patterns. They are a review aid, not a comprehensive secret scanner or proof that publication is authorized.
