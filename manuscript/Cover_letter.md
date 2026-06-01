Chihwa Lee
Korean National Police Agency, AI Policy Division; KAIST
[email] · ORCID 0009-0009-6959-1797
[Date]

To the Editors, *Scientific Data* (Nature Portfolio)

Dear Editors,

We submit our Data Descriptor, **"A survey-anchored synthetic persona dataset with crime-prevention behavioral attributes for Korean police-administration research"** (the KVRB dataset), for consideration.

Demographically realistic synthetic populations of Koreans already exist, but they lack the behavioral and victimization variables that crime-prevention research turns on. KVRB adds that layer to a one-million-record backbone by **sampling each behavioral attribute from a real Korean national survey conditional and using a language model only to render the sampled value into narrative — never to estimate it**. This "render-not-estimate" design keeps the behavioral layer anchored to official statistics rather than to model priors.

We believe the dataset fits *Scientific Data* for three reasons. First, it is a reusable resource with fully documented provenance: every attribute names its survey anchor, conditioning cells, and strength tier. Second, the technical validation is unusually candid about what the construction does and does not establish — distributional fidelity is reported as a by-construction check of the sampler, narrative round-trip reliability is reported honestly (including a mediocre 0.730 kappa for digital literacy), and, most importantly, the inter-attribute **joint is validated out-of-sample for the elderly cohort against a same-respondent survey not used as an anchor, quantifying the conditional-independence error (2.36× the independence baseline; 95% CI 2.20–2.55)** rather than asserting joint validity. Third, the descriptor states its limits at the schema level — including that the elderly digital-literacy marginal is currently a within-cohort ordinal measure, not a population prevalence, pending recalibration — so reusers know exactly how far to trust each field.

All code, anchor tables, and the technical-validation outputs are openly released (MIT for code, CC-BY-4.0 for derived data and documentation); the dataset is archived at Zenodo with a citable DOI, and the backbone is reproducible from its pinned upstream release. No record corresponds to a real person, and the release abstracts operational thresholds to limit dual-use exposure.

This manuscript is original, not under consideration elsewhere, and the author has approved the submission. The author declares no competing interests. We have no preferred or excluded reviewers to suggest beyond the journal's discretion.

Thank you for considering our submission.

Sincerely,

Chihwa Lee
Korean National Police Agency, AI Policy Division; KAIST
