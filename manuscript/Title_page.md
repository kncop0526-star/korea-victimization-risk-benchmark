# Title Page

**Title:** A survey-anchored synthetic persona dataset with crime-prevention behavioral attributes for Korean police-administration research

**Manuscript type:** Data Descriptor (Scientific Data, Nature Portfolio)

**Authors:** Chihwa Lee¹*

**Affiliations:**
¹ Korean National Police Agency, AI Policy Division; KAIST, Daejeon, Republic of Korea

**\* Corresponding author:** Chihwa Lee, chi0526@kaist.ac.kr; ORCID: 0009-0009-6959-1797

---

**Summary (for submission system; ~150 words).**
KVRB (Korea Victimization-Risk persona Benchmark) is a one-million-record synthetic Korean persona dataset that adds a crime-prevention behavioral layer — financial vulnerability, digital literacy, authority deference, social isolation, prior victimization, reporting propensity — to NVIDIA's demographically faithful Nemotron-Personas-Korea backbone. Each behavioral attribute is sampled from the conditional distribution of a real Korean national survey, and a pinned language model only renders the sampled value into first-person narrative; the model expresses values, it does not estimate them. Marginal-by-cell fidelity holds by construction; the inter-attribute joint is modeled partially (one observed survey joint plus shared-demographic conditioning) and adjudicated out-of-sample, for the elderly cohort, against a same-respondent survey that quantifies the conditional-independence error. The release comprises the enriched dataset, construction code, anchor tables with survey provenance, and a technical validation. The dataset supports cohort construction, agent-based simulation, and prevention-message testing without contact with real individuals.

**Keywords:** synthetic population; data fusion; survey conditioning; behavioral attributes; crime prevention; Korea; large language models

**Competing interests:** The author declares no competing interests.

**Funding:** None.
