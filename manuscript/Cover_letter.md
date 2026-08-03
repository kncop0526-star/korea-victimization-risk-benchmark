Chihwa Lee
Korean National Police Agency, AI Policy Division; KAIST
chi0526@kaist.ac.kr · ORCID 0009-0009-6959-1797

To the Editors, *Journal of Artificial Societies and Social Simulation*

Dear Editors,

I am submitting the manuscript **"Survey-Anchored Synthetic Populations with Behavioral Attributes for Agent-Based Social Simulation: Data Fusion, Out-of-Sample Validation, and Which Fused Structure a Model Needs"** for consideration as a research article.

Agent-based models increasingly depend on populations whose agents differ in behavior, not only in demographics. Building such a population is a data-fusion problem: the behavioral attributes worth simulating live in separate surveys that share no respondents, so their joint distribution cannot be identified and is usually assumed under conditional independence and never checked. Chapuis, Taillandier and Drogoul's review in this journal (2022) names exactly this by-construction validation as the field's recurring weakness. The manuscript answers that critique not with another marginal check but by carrying the validation outside the source data and into a model.

Concretely, the paper constructs a one-million-record synthetic population of Korea and labels every inter-attribute pair as measured or assumed. It validates the assumed joint out-of-sample against an independent same-respondent survey, where real elderly co-occurrence runs at 2.30 times the independence baseline against the released 1.29. A controlled agent-based experiment then decomposes which part of the fused structure a model actually responds to, and the result is non-obvious. Demographic coupling drives aggregate simulation outcomes, whereas the cross-survey inter-attribute joint that fusion cannot identify is second-order for aggregate outcomes yet first-order for distributional ones: it governs who is left unreached. The ordering replicates under a second mechanism, bounded-confidence opinion dynamics, and on a community-structured network. The paper is candid about the single assumed-joint validation locus and the stylized model as scoped limitations rather than settled generality.

The work is committed to open, reproducible social simulation: the population, the survey-derived anchor tables, and all construction, validation, and simulation code are openly released under permissive licenses, with the two agent-based models documented in ODD-protocol form.

The manuscript is original, is not under consideration elsewhere, and reports no competing interests. Thank you for your consideration.

Sincerely,
Chihwa Lee
