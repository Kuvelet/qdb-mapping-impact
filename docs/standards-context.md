# ACES, PIES, and Qdb: Where This Project Fits

## Qdb in Plain Language

**Qdb stands for Qualifier Database**, an Auto Care Association reference database supporting ACES. It provides coded fitment expressions, including parameterized expressions for variable values. It is not a catalog of every manufacturer's parts or a service that independently determines whether a part fits. [Auto Care Qdb overview](https://www.autocare.org/data-and-information/data-standards/databases/qualifier-database-qdb).

Think of a qualifier as an important condition attached to an application record. The task is to preserve that condition while expressing it consistently. Mapping must not broaden or narrow the original meaning accidentally.

### A Simple Example

The following phrases and templates are **invented teaching examples**, not published Qdb records, IDs, or approved mappings:

| Source note | What a reviewer must establish | Conceptual structured representation |
|---|---|---|
| `W/ aux filter` | Does this mean the same condition as "With auxiliary filter" in this application? | An appropriate qualifier, if one exists and preserves that meaning |
| `After serial 1000` | Which serial number, and is the boundary exclusive or inclusive? | An appropriate qualifier plus the reviewed value `1000` |
| `Serial 1000 through 2000` | Which serial range and endpoint rules apply? | An appropriate qualifier plus two reviewed values |

This illustrates why the Python project has no-, single-, and dual-parameter workflows. Those scripts enter the supplied selections and values; they do not answer the review questions in the middle column. A real mapping requires authorized reference data and application context. Some conditions should be expressed through vehicle attributes or another standard structure instead of Qdb.

## Why It Matters in the Aftermarket

The aftermarket includes replacement and service parts offered through many suppliers and selling channels. Fitment information must travel with the product: a complete product description alone cannot establish the correct application. ACES provides an exchange standard for fitment data used by manufacturers, distributors, retailers, and other trading partners. [Auto Care ACES overview](https://www.autocare.org/aces).

Auto Care identifies more consistent interpretation, validation, partner loading, and part selection as benefits of coded qualifiers. These are reasons to invest in mapping, not results independently demonstrated by this project. [Qdb business benefits](https://www.autocare.org/data-and-information/data-standards/databases/qualifier-database-qdb).

For this case study, the business implications are:

| Audience | Why the work matters | How this project supports it |
|---|---|---|
| Catalog specialists | Repeated note text creates recurring review and entry work | A unique-note backlog, description priorities, and attended Python entry workflows |
| Data recipients | Inconsistent wording can require interpretation when content is exchanged | A mapping process aimed at more consistent qualifier representation; downstream acceptance still needs checking |
| Counter staff and online shoppers | A missing or misunderstood condition can affect part selection | Qualifier review intended to preserve the application constraints; actual lookup outcomes are not measured here |
| Catalog managers | Mapped-note totals alone do not explain how much of the catalog is involved | SQL measures repeated cells, distinct application rows, and current versus potential reach |

**Catalog health is broader than mapped status.** A standardized but incorrect qualifier is still a defect. Correct vehicle configurations, complete product data, valid parameters, deployment, and downstream presentation all remain important. This report measures the note-mapping work and its occurrence footprint, not an overall catalog-quality score. See the [business case and measurement plan](business-case.md).

## Keep the Roles Separate

| Component | Role in the standards ecosystem | Relationship to this project |
|---|---|---|
| ACES: Aftermarket Catalog Exchange Standard | Communicates product fitment information: which applications a part is cataloged for | The mapping initiative concerns application qualifiers |
| Qdb: Qualifier Database | Standardized, coded fitment qualifier terminology used with ACES | Python applies supplied Qdb text and parameter values through PIM; SQL measures source-note occurrence. Neither validates qualifier semantics or reference-version compatibility. |
| VCdb | Vehicle and equipment configurations and attributes supporting ACES | Supplies standardized fitment context outside this report's scope |
| PIES: Product Information Exchange Standard | Communicates product information such as attributes, descriptions, and other product content | Complementary to fitment quality; not parsed or validated by this report |
| PAdb | Standardized product attributes supporting PIES | Not interchangeable with Qdb qualifier mapping |
| PCdb / Brand Table | Shared product-classification and brand reference information | Not imported or validated by this project |

Primary references: [Auto Care ACES](https://www.autocare.org/aces), [PIES](https://www.autocare.org/pies), [Qdb](https://www.autocare.org/data-and-information/data-standards/databases/qualifier-database-qdb), and [Auto Care standards FAQ](https://www.autocare.org/about-us/frequently-asked-questions).

## Why Map Free Text to Qdb?

Qdb provides coded expressions for application qualifiers, including parameterized expressions where variable values belong in placeholders. That structure can make recurring qualification text more consistent and more amenable to validation than unrestricted wording. [Auto Care Qdb documentation overview](https://www.autocare.org/data-and-information/data-standards/databases/qualifier-database-qdb).

An illustrative, invented note such as "With auxiliary filter" expresses an application condition. A reviewer must establish what that condition means and whether an available qualifier represents it accurately. This example is not an official Qdb term, identifier, or recommended mapping.

Mapping is not simply replacing one string with another. Review may need to resolve abbreviations, multiple conditions, exceptions, parameters, units, or ambiguity. Some source content may belong in a vehicle attribute, a product attribute, or another field rather than a qualifier. An exact text match to a source cell establishes occurrence only; it does not establish the correct target representation.

Auto Care's published practitioner presentation outlines collecting notes, cleaning and reviewing the list, comparing it with Qdb, and addressing remaining gaps. It separately discusses PIES attributes. The report here supports assessment and prioritization around that human review, rather than replacing it. [Free Your ACES/PIES from Free-Form Text](https://www.autocare.org/docs/default-source/events/event-materials/acpn/08---free-your-aces-pies-from-free-form-text.pdf).

## What the Tracker Actually Knows

The core report consumes only note text, its `MappingStatus`, and the selected application fields. A source mapping workbook may contain proposed qualifier text, parameters, units, and reviewer notes, but these are not validated by the report.

The inspected Python scripts add an execution layer: they apply Qdb text and parameters supplied in Excel through the PIM interface. They do not generate candidates, score confidence, validate qualifier IDs against a release, or verify the persisted mapping after Save. They require manual login and reviewed mapping instructions. See the [Python automation guide](python-automation.md).

| The tracker can establish | The tracker cannot establish |
|---|---|
| A listed note exactly occurs in a searched cell | The note is semantically equivalent to a proposed qualifier |
| A note's status says Mapped | The target qualifier ID exists and is valid for a reference release |
| The same text appears under several descriptions | The same mapping is appropriate in every context |
| A row contains at least one mapped-status note | The application is fully standardized or free of other defects |
| A description has many matching occurrences | It has the greatest financial value or highest safety risk |

## The Connection to PIES

A catalog user needs both useful product information and usable fitment information. Improving qualifier governance can complement work on product attributes, descriptions, and related content by giving the organization a consistent review discipline.

However, **Qdb mapping is not PIES attribute mapping**. The current code does not check PAdb identifiers, product-attribute completeness, images, packaging, pricing, or PIES file structure. A PIES-specific extension would require a different input contract and validation rules. Calling this an "ACES/PIES validator" or a "PIES compliance engine" would misrepresent the implementation.

The most accurate portfolio positioning is: **a Python-based Qdb mapping automation project with SQL analysis of low-confidence notes, mapping progress, and catalog impact, within the broader ACES/PIES ecosystem.** The tracker is the analytics deliverable, not the entire project.

## What Completion Means

"100% mapped" means every unique note in the report has mapped status. It does not mean every application is correct, every free-text field is removed, every mapping is deployed, or every ACES/PIES requirement is satisfied.

Similarly, a note that has no match in the searched fields is not automatically invalid. The note may differ in case or formatting, occur in an excluded field, be embedded in a longer string, or come from a different source snapshot. These are possible explanations to investigate, not automatic conclusions about the data.

## Version and Licensing Boundaries

The public tracker contains no reference database records, qualifier identifiers, schemas, or example ACES/PIES payloads presented as validated standards output. Its synthetic demo does not need licensed reference content.

For real mapping work, use the organization's authorized reference releases and documentation. Auto Care announced ACES 5.0 and PIES 8.0, together with reference-schema updates, in April 2026; this report is not a claim of certification against those versions. [Official release announcement](https://www.autocare.org/news/latest-news/details/2026/04/02/auto-care-association-releases-aces--5.0-and-pies--8.0).

Record the actual ACES/PIES target versions and Qdb release used by the organization. They were not supplied for this case study. Public-source context was checked on September 14, 2026; it should be rechecked when standards context is updated.
