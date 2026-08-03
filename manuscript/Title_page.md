# Title Page

**Title:** Survey-Anchored Synthetic Populations with Behavioral Attributes for Agent-Based Social Simulation: Data Fusion, Out-of-Sample Validation, and Which Fused Structure a Model Needs

**Manuscript type:** Research article

**Target journal:** Journal of Artificial Societies and Social Simulation (JASSS)

**Author:** Chihwa Lee¹*

**Affiliation:**
¹ Korean National Police Agency, AI Policy Division; KAIST, Daejeon, Republic of Korea

**\* Corresponding author:** Chihwa Lee · chi0526@kaist.ac.kr · ORCID 0009-0009-6959-1797

---

**Abstract.**
Agent-based models of social processes need populations whose agents differ not only in demographics but in behavior and attitude, yet demographic synthetic populations rarely carry those attributes, so modelers assign them by assumption. This paper constructs and validates a one-million-record synthetic population of Korea that adds six survey-anchored behavioral attributes (financial vulnerability, digital literacy, authority deference, social isolation, prior victimization, reporting propensity) to a demographically faithful backbone. Each attribute is sampled from the conditional distribution of a real national survey given a demographic cell, and every inter-attribute pair is labeled measured, when observed on shared respondents, or assumed, when combined under conditional independence. The assumed joint is tested out-of-sample against an independent same-respondent survey: real elderly co-occurrence runs at 2.30 times the independence baseline where the released population reaches 1.29. A controlled diffusion experiment then asks which part of the fused structure changes model outcomes. Demographic coupling carries the aggregate effect. The cross-survey inter-attribute joint is, for the attributes the model uses, conditionally independent by construction, so removing it directly is a null-control; the substantive test injects the externally observed dependence (2.30 times) and finds aggregate reach shifts by at most 1.3 points. That inertness is outcome-specific: the same dependence cuts the count of never-reached agents by a quarter to a half where the process leaves an unreached remainder. The ordering reappears under bounded-confidence opinion dynamics and on a community-structured network. The conditional-independence assumption is therefore safe for aggregate conclusions and unsafe for distributional ones, and the labeling-plus-external-validation-plus-decomposition procedure determines which. The population, anchors, and code are openly released.

**Keywords:** synthetic populations; agent-based modeling; data fusion; statistical matching; survey conditioning; out-of-sample validation

**Competing interests:** The author declares no competing financial interests or personal relationships that could have influenced the work.

**Funding:** None.

**Data and code availability:** Enriched dataset, survey-derived anchor tables, and all construction, validation, and simulation code are openly available on Zenodo (DOI 10.5281/zenodo.20500537) and GitHub (https://github.com/kncop0526-star/korea-victimization-risk-benchmark), under MIT (code) and CC-BY-4.0 (derived data and documentation). The NVIDIA Nemotron-Personas-Korea backbone (CC-BY-4.0) is not redistributed and is reproducible from the pinned upstream revision.

**Generative-AI disclosure:** During manuscript preparation the author used Claude (Anthropic) to assist with drafting and editing under the author's direction; the methodological use of a language model to render narratives is described in Section 3.3. The author takes full responsibility for the content.
