# Assumptions

- Use a 3-hop Alzheimer's neighborhood restricted to mechanistic and indication relations: it retains drug–protein–protein–disease routes without anatomy and drug-interaction hubs expanding the entire graph.
- At the stage-2 checkpoint, embedding-only and combined metrics remain unavailable until stage 5: inventing scores or relabeling path scores would misrepresent progress.
- Independently tested trial drugs are retrieval targets, not positive efficacy labels: a trial can fail or have no posted results.
- Remove all graph relationships between held-out drugs and resolved Alzheimer's disease nodes before selecting the neighborhood: this also prevents direct-label leakage through reverse or alternative relations.
- Use a deterministic evaluation split and fixed ranking parameters: held-out labels are not used to tune ranking weights.
- Hold out every target-disease/drug pair, not only matched trial drugs: this prevents unrecognized trial labels and reverse relations from informing graph rankings.
- Include drugs with a non-Alzheimer indication in the fixed universe, even if unreachable: this avoids silently dropping hard held-out candidates; indication is not proof of regulatory approval.
- Retain existing Alzheimer drugs as possible rediscovery controls at this checkpoint: approval status must be verified before presenting a novel repurposing-only list.
- Require completed/terminated interventional treatment trials, actual enrollment >0, and experimental-arm drugs: planned studies and routine background comparators do not establish testing evidence.
- Exact normalized names or trial-provided aliases only: conservative matching avoids falsely assigning a trial to the wrong drug.
- PrimeKG relation endpoints do not establish biological action direction or numerical evidence confidence: export unknown direction and use uniform edge weights.
- Use a retrospective holdout rather than a time split: the snapshot lacks sufficient per-edge dates to enforce temporal exclusion honestly.
- MRR uses reciprocal first relevant rank for the one disease query; report mean reciprocal held-out drug rank separately to expose performance beyond the first hit.
- Random baseline averages 1,000 fixed-seed permutations (0–999): a single random permutation would be unstable for 48 positives in 1,801 candidates.
- Maintain context.md after meaningful changes: the user requested a durable handoff record for another model.
