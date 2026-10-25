# Q&A cheat sheet

Research hypothesis, not medical advice. This tool does not tell anyone what to
take. Talk to a doctor or pharmacist about any medicine.

Honest answers to the questions this project should be asked. If a question is not
here, the safe answer is "I don't know, and here is what we actually measured."

---

**So does it work?**

On the primary, audited evaluation it found **1 of 24** trial-tested Alzheimer's
drugs in its top 20 — 4.17%, exact 95% CI 0.11–21.12%. That interval is almost the
whole plausible range, because 24 labels is a tiny sample. The honest answer is that
this is a weak positive at best and we cannot distinguish it from chance.

**You said 4 of 44 before. What changed?**

We audited the labels. The raw label set counted any drug appearing in an
Alzheimer-tagged completed trial record. Reading those records one by one against a
rule frozen *before* we looked, most did not qualify: healthy-volunteer probes, PK
studies, background medication, cohorts that were not actually diagnosed patients.
That took 44 labels to 24 and 4 hits to 1. The raw figure is still reported as
secondary, because it is true of the raw set — it was just measuring something looser
than "the drug was studied as a treatment in people with this disease."

**What survived?**

One insulin. Insulin glulisine. Insulin aspart and insulin detemir became *uncertain*
because their population evidence was ambiguous, and choline was excluded outright.
We had been saying "the recovery is essentially insulin" for weeks as a caveat; under
audit that turned out to understate it.

**Isn't excluding the ambiguous ones convenient?**

That is exactly why we wrote down how to handle them *before* computing anything
(`docs/STRICT_LABEL_PROTOCOL.md`). Uncertain records are excluded from the primary
set and included in a pre-declared sensitivity analysis, and we always report both.
The sensitivity answer is 3 of 32, 9.38%. If you prefer that reading, take it — it is
on the same page and in the same artifact.

**What is the p-value?**

Family-aware permutation p@20 is **0.233** on the strict set, 0.287 on the
sensitivity set, and 0.080 on the raw set. So the one number that looked suggestive
stopped looking suggestive once the labels were audited. All of these are exploratory
and unadjusted; we did not pre-register a significance threshold and you should not
read one in.

**Did the embeddings help?**

No. A fixed DistMult model scored **0 of 22** at recall@10 and @20 on the reserved
split, and the mixture tuning selected zero weight for it. We kept the result and
reported it rather than dropping the experiment.

**Your top candidate is mecamylamine. Isn't that a nicotinic antagonist?**

Yes, and that is the most useful thing in the demo. Path scoring reads an undirected,
unsigned graph — it sees that mecamylamine connects to the right receptors and cannot
see which way it pushes. The literature agents caught what the score could not: in the
retrieved animal work, mecamylamine *abolished* nicotine's cognitive benefit. The
ranking's top hit may well point the wrong way. We show that rather than hiding it.

**So the ranking has no idea about direction?**

Correct, and that is a property of the data, not a bug we can patch. PrimeKG edges
carry no direction and no sign. Every edge in the UI is labelled "direction unknown".

**How do you know the agents aren't making up citations?**

Every claim must carry a PMID that was in that family's retrieved set *and* a verbatim
8–40 word quote that appears in that record's title or abstract. A deterministic
checker verifies the span after normalising case, whitespace and unicode punctuation.
Across the cached top 20: **229 of 231 claims verified, 2 flagged (0.87%)** — and both
failures were quote-length violations, not invented PMIDs. Anything unverified is
shown as unverified and never as support.

**The gap-map verdicts — how are those decided?**

Keyword heuristics over the agents' structured output, and we say so on the page. They
classify what *kind* of record was cited, not whether the evidence is about
Alzheimer's or which way it points. We audited all 20 against their own quotes: 16
agree, 4 do not, and the four are listed by name in `docs/METHODOLOGY.md`. That audit
is a **self-audit on the same families the rules were tuned on**, so treat its
agreement rate as an upper bound.

**Did it generalise to another disease?**

No. We ran the identical method, unchanged, on Parkinson's: **0 of 24** strict labels
and 0 of 39 raw labels in the top 20. We are reporting that because it failed, not
because it succeeded. There is no Parkinson's product — no candidate list, no agents,
no selector — only a static table.

**Who checked the label decisions?**

Two independent reviewers, each in a fresh context with only the frozen rule, the
rank-free source records and the decision file — no ranks, no scores, no metrics.
Agreement was 52/57 (κ = 0.856) for Alzheimer's and 55/56 (κ = 0.961) for Parkinson's.
Every disagreement was demoted to uncertain by the pre-declared rule. Two careful
readings agreeing is still not proof either is right, which is why
`docs/HUMAN_CHECKS.md` lists 15 decisions for a person to verify by hand.

**What would change your mind / what would you do next?**

A prospective test. Everything here is retrospective: the graph was built from data
that already contains the answers in some diffuse form. The real test is to freeze
today's ranking, wait for trials that have not run yet, and score against those. Also
worth doing: a larger label set, a directed or signed interaction source so the
ranking can tell agonist from antagonist, and a second disease where the method is
given a fair chance rather than bolted on.

**Is any of this clinically useful?**

Not yet, and nothing here should be read as a treatment recommendation. The useful
part is the inspectable chain — you can click any candidate, see the exact
drug → protein → disease path, read the quotes behind every claim, and see the
objection an agent raised against it. The value is auditability, not the ranking.

**What's the single biggest weakness?**

Sample size. 24 labels, one hit, one family. Every conclusion here is one or two
records away from changing, which is why the intervals are wide and stated everywhere
and why the headline carries "very small sample" and "small test, not shown to
generalize."
