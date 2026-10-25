# Phase 1 raw trial-label audit

> Research hypothesis, not medical advice. This tool does not tell anyone what to take. Talk to a doctor or pharmacist about any medicine.

This is a source audit of the **pre-rule labels**, not a treatment recommendation, effectiveness assessment, or application of a new eligibility rule. A ClinicalTrials.gov condition tag is a search/indexing field; it does **not** establish that every enrolled participant had that condition. The classifications below describe what the saved registry records allow us to say about enrollment and the drug's role. They do not classify trial results.

## Provenance and inherited selection

- Source snapshots: `data/raw/trials.json`, queried for `Alzheimer Disease`, retrieved 2026-10-24 18:48:31 UTC (2,615 studies, 3 pages); and `data/raw/parkinsons/trials.json`, queried for `Parkinson Disease`, retrieved 2026-10-25 04:52:49 UTC (2,922 studies, 3 pages). Both identify `https://clinicaltrials.gov/api/v2/studies` as source and record API `filter.overallStatus=COMPLETED,TERMINATED`. This audit used only those saved records; no live registry query.
- Existing label files: `artifacts/diseases/alzheimers/trial_labels.json` (44 labels, 59 stored drug–trial entries, 57 distinct drug/NCT pairs, 53 distinct NCTs) and `artifacts/diseases/parkinsons/trial_labels.json` (39 labels, 57 stored entries, 53 distinct pairs, 48 distinct NCTs). The files report 576/547 trials passing the inherited trial gate, 79/71 total matched drugs, and 31/15 drugs excluded outside their candidate universes, respectively. Those are artifact metadata, not recomputed outcomes. Duplicate entries arise when one drug is registered in multiple experimental arms of the same NCT.
- The existing `src/repurpose/data.py:fetch_trials` API request filters status to completed or terminated. `match_trials` then requires a condition *string* matching the disease pattern (case insensitive), `INTERVENTIONAL` study type, `COMPLETED` or `TERMINATED` status, `ACTUAL` enrollment greater than zero, and `TREATMENT` primary purpose. It considers only `DRUG` interventions linked to an `EXPERIMENTAL` arm. It normalizes drug names by case folding and removing non-alphanumeric characters, matches an intervention name or `otherNames` to a drug node's name exactly after that normalization, and accepts only a unique drug hit. The saved label artifacts additionally reflect a candidate-universe exclusion and list control IDs, but the inspected matcher does not itself implement either downstream step. None of these inherited filters checks the actual enrollment diagnosis, healthy-volunteer flag, pharmacokinetic/probe role, or disease-specific outcome.
- `NA` phase and absent healthy-volunteer fields below mean the registry snapshot records no value. They should not be interpreted as clinical findings. All quoted eligibility snippets are explicitly marked **Registry quote**. Design notation is phase; allocation/model, with `TREATMENT` primary purpose for every listed trial.

## First ten Alzheimer’s labels by ascending `drug_id`

The table lists every distinct supporting NCT for each of the first ten labels. Shared NCT00245206 appears for three drugs; NCT01547169 is stored twice for two insulin-detemir experimental arms.

| Drug ID / drug | NCT | Enrollment evidence | Registry condition tags; phase | Drug intervention and role | Design |
|---|---|---|---|---|---|
| 14161 Olanzapine | [NCT00245206](https://clinicaltrials.gov/study/NCT00245206) | Registry quote: “DSM-IV diagnosis of a disease or disorder that requires treatment with an atypical antipsychotic medication.” Healthy flag `true`; AD diagnosis is not required by this text. | Schizophrenia; Alzheimer's Disease; Dementia; PHASE4 | Olanzapine, experimental antipsychotic arm; psychiatric-disorder population | Randomized parallel |
| 14179 Raloxifene | [NCT00368459](https://clinicaltrials.gov/study/NCT00368459) | Registry quote: “criteria for probable Alzheimer's disease (AD) based on results of a neurologist's evaluation and laboratory tests.” | Alzheimer Disease; PHASE2 | Raloxifene, experimental arm | Randomized parallel |
| 14218 Lamivudine | [NCT04552795](https://clinicaltrials.gov/study/NCT04552795) | Registry quote: “Clinical diagnosis of early Alzheimer's disease (Clinical Dementia Rating (CDR) = 0.5, Mini-Mental State Exam (MMSE) = 24-30).” | Alzheimer Disease, Early Onset; PHASE1/PHASE2 | Registered as `3TC`, an experimental single-arm drug matched by alias to lamivudine | Single group; allocation NA |
| 14223 Risperidone | [NCT00245206](https://clinicaltrials.gov/study/NCT00245206) | Registry quote: “DSM-IV diagnosis of a disease or disorder that requires treatment with an atypical antipsychotic medication.” Healthy flag `true`; AD diagnosis is not required by this text. | Schizophrenia; Alzheimer's Disease; Dementia; PHASE4 | Risperidone, experimental antipsychotic arm | Randomized parallel |
| 14271 Isotretinoin | [NCT01560585](https://clinicaltrials.gov/study/NCT01560585) | Registry quote: “Probable AD by DSM IV and NINCDS-ADRDA criteria.” | Alzheimer's Disease; PHASE1/PHASE2 | Isotretinoin, open-label experimental arm | Single group; allocation NA |
| 14286 Rifampicin | [NCT00439166](https://clinicaltrials.gov/study/NCT00439166) | Registry quote: “Diagnosis of probable Alzheimer's disease by NINCDS-ADRDA criteria.” | Alzheimer's Disease; PHASE3 | Rifampicin, experimental rifampin-only and combined doxycycline/rifampin arms | Nonrandomized factorial |
| 14306 Pioglitazone | [NCT00982202](https://clinicaltrials.gov/study/NCT00982202) | Registry quote: “Clinical Dementia Rating (CDR) score of 1 or 2 (mild to moderate AD severity) at both screening and baseline.” | Alzheimer Disease; PHASE2 | Pioglitazone, experimental `PGZ` arm | Randomized parallel |
| 14306 Pioglitazone | [NCT01931566](https://clinicaltrials.gov/study/NCT01931566) | Registry quote: “Is cognitively normal at baseline”; healthy flag `true`. This is risk/prevention enrollment, not diagnosed AD enrollment. | Mild Cognitive Impairment Due to Alzheimer's Disease; PHASE3 | Pioglitazone, experimental high-risk prevention arm | Randomized parallel |
| 14306 Pioglitazone | [NCT02284906](https://clinicaltrials.gov/study/NCT02284906) | Registry quote: “Completed the pivotal AD-4833/TOMM40\_301 study with an adjudicated diagnosis of mild cognitive impairment (MCI) due to Alzheimer's Disease (AD).” | Mild Cognitive Impairment Due to Alzheimer's Disease; PHASE3 | Pioglitazone, experimental extension arm | Nonrandomized parallel |
| 14323 Aripiprazole | [NCT00245206](https://clinicaltrials.gov/study/NCT00245206) | Registry quote: “DSM-IV diagnosis of a disease or disorder that requires treatment with an atypical antipsychotic medication.” Healthy flag `true`; AD diagnosis is not required by this text. | Schizophrenia; Alzheimer's Disease; Dementia; PHASE4 | Aripiprazole, experimental antipsychotic arm | Randomized parallel |
| 14329 Insulin detemir | [NCT01547169](https://clinicaltrials.gov/study/NCT01547169) | Registry quote: “Diagnosed with mild cognitive impairment, or mild/moderate AD.” | Alzheimer's Disease; Mild Cognitive Impairment; PHASE2 | Insulin detemir, two experimental intranasal-dose arms (two stored entries) | Randomized parallel |
| 14329 Insulin detemir | [NCT01595646](https://clinicaltrials.gov/study/NCT01595646) | Registry quote: “Diagnosed with mild cognitive impairment, or mild/moderate AD.” | Alzheimer's Disease; Mild Cognitive Impairment; PHASE2 | Insulin detemir, experimental intranasal arm | Randomized parallel |
| 14402 Pitavastatin | [NCT00548145](https://clinicaltrials.gov/study/NCT00548145) | Registry quote: “Alzheimer's Disease patients”; eligibility also requires MMSE 15–23, CDR 1 or 2, and hypercholesterolemia. | Alzheimer Disease; Hypercholesterolemia; NA | Pitavastatin, experimental arm | Randomized parallel |

The saved design field records **no masking** for NCT00245206, NCT04552795, NCT01560585, and NCT00548145; it records **quadruple masking** for the other NCTs in this Alzheimer’s sample.

## First ten Parkinson’s labels by ascending `drug_id`

| Drug ID / drug | NCT | Enrollment evidence | Registry condition tags; phase | Drug intervention and role | Design |
|---|---|---|---|---|---|
| 14144 Topiramate | [NCT00794313](https://clinicaltrials.gov/study/NCT00794313) | Registry quote: “Parkinson's Disease”; also requires oral levodopa and dyskinesias. | Parkinson's Disease; NA | Topiramate in experimental amantadine-plus-topiramate arm | Randomized crossover |
| 14154 Acetaminophen | [NCT02305017](https://clinicaltrials.gov/study/NCT02305017) | Registry quote: “Subjects who are healthy as determined by pre-study medical history, physical examination, vital signs, complete neurological examination and 12-lead ECG.” Healthy flag `true`. | Parkinson's Disease; PHASE1 | Registered as paracetamol, a coadministered PK interaction probe with opicapone | Randomized crossover |
| 14180 Buspirone | [NCT02589340](https://clinicaltrials.gov/study/NCT02589340) | Registry quote: “Parkinson's disease diagnosis”; levodopa and dyskinesia also required. | Parkinson's Disease; Dyskinesias; Movement Disorders; PHASE1 | Buspirone, experimental arm with background amantadine | Randomized crossover |
| 14180 Buspirone | [NCT02803749](https://clinicaltrials.gov/study/NCT02803749) | Registry quote: “Diagnosis of idiopathic PD by UK Parkinson's Disease Society Brain Bank Clinical Diagnostic Criteria.” | Parkinson Disease; Anxiety; PHASE2 | Buspirone, experimental anxiety-treatment arm | Randomized parallel |
| 14189 Nortriptyline | [NCT00062738](https://clinicaltrials.gov/study/NCT00062738) | Registry quote: “Parkinson's disease without dementia.” Depression is also required. | Parkinson Disease; Depression; PHASE2 | Nortriptyline, experimental antidepressant arm | Randomized parallel |
| 14216 Warfarin | [NCT02169440](https://clinicaltrials.gov/study/NCT02169440) | Registry quote: “Healthy as determined by pre-study medical history, physical examination, vital signs, complete neurological examination and 12-lead ECG.” Healthy flag `true`. | Parkinson's Disease (PD); PHASE1 | Warfarin, PK/PD interaction substrate for BIA 9-1067 | Randomized crossover |
| 14216 Warfarin | [NCT02305030](https://clinicaltrials.gov/study/NCT02305030) | Registry quote: “Healthy as determined by pre-study medical history, physical examination, vital signs, complete neurological examination and 12-lead electrocardiogram (ECG).” Healthy flag `true`. | Parkinson's Disease; PHASE1 | Warfarin, steady-state opicapone interaction substrate | Nonrandomized single group |
| 14259 Repaglinide | [NCT01536366](https://clinicaltrials.gov/study/NCT01536366) | Registry quote: “Healthy as determined by pre-study medical history, physical examination, vital signs, complete neurological examination and 12-lead ECG.” Healthy flag `true`. | Parkinson Disease; PHASE1 | Repaglinide, PK interaction substrate for BIA 9-1067 | Randomized crossover |
| 14286 Rifampicin | [NCT04070495](https://clinicaltrials.gov/study/NCT04070495) | Healthy flag `true`; Registry quote (exclusion): “Subjects with any current disease requiring treatment.” | Parkinson's Disease; PHASE1 | Rifampicin, interaction perpetrator in KW-6356 study | Nonrandomized single group |
| 14298 Rosuvastatin | [NCT03970798](https://clinicaltrials.gov/study/NCT03970798) | Healthy flag `true`; Registry quote (exclusion): “Individuals with any current disease requiring treatment.” | Parkinson's Disease; PHASE1 | Rosuvastatin, index-substrate probe in KW-6356 interaction study | Single group; allocation NA |
| 14299 Sertraline | [NCT01437189](https://clinicaltrials.gov/study/NCT01437189) | Registry quote: “All patients should have a confirmed diagnosis of PD according to Brain Bank Criteria.” Depression also required. | Depression; Parkinson's Disease; NA | Sertraline, experimental antidepressant arm | Single group; allocation NA |
| 14306 Pioglitazone | [NCT01280123](https://clinicaltrials.gov/study/NCT01280123) | Registry quote: “Men and women with idiopathic PD of less than 5 years duration from diagnosis.” | Parkinson's Disease; PHASE2 | Pioglitazone, two experimental dose arms | Randomized parallel |

The saved design field records **double masking** for NCT00794313; **quadruple masking** for NCT02589340, NCT02803749, NCT00062738, and NCT01280123; and **no masking** for the remaining NCTs in this Parkinson’s sample.

## Per-label audit of all raw labels

`C` = **clear all-supporting concern**: every saved supporting trial for that drug is clearly healthy-volunteer, interaction/probe, PK-only, or an enrollment/condition mismatch for a diagnosed-disease treatment label. `M` = **mixed or unresolved**: at least one source has a mixed population, a healthy flag inconsistent with disease-specific criteria, a co-treatment/other-condition target, or another enrollment ambiguity; this is not a finding that all sources are ineligible. `D` = **disease-enrollment evidence present without a clear concern from the four audited categories** in the saved supporting source(s). `D` is not a claim of benefit or a strict-rule pass. All classifications are at the **label** level, so an `M` label may also have a clearly problematic individual trial.

| Disease | C | M | D | Total |
|---|---:|---:|---:|---:|
| Alzheimer’s | 4 | 19 | 21 | 44 |
| Parkinson’s | 10 | 7 | 22 | 39 |

### Alzheimer’s: all 44 labels

| Drug ID / name | Audit | Source reason |
|---|:---:|---|
| 14161 Olanzapine | M | NCT00245206 enrolls a general antipsychotic-requiring disorder; AD diagnosis is not required, despite AD condition tag. Healthy flag is also `true`, conflicting with disorder-focused criteria. |
| 14179 Raloxifene | D | NCT00368459 requires probable AD. |
| 14218 Lamivudine | D | NCT04552795 requires a clinical early-AD diagnosis; drug is registered as 3TC. |
| 14223 Risperidone | M | Same general-disorder/healthy-flag ambiguity as olanzapine in NCT00245206. |
| 14271 Isotretinoin | D | NCT01560585 requires probable AD. |
| 14286 Rifampicin | D | NCT00439166 requires probable AD; rifampicin has combined and single-drug arms. |
| 14306 Pioglitazone | M | NCT00982202 has AD enrollment, NCT02284906 has MCI due to AD, but NCT01931566 enrolls cognitively normal people for risk/prevention despite the AD-family condition tag. |
| 14323 Aripiprazole | M | Same general-disorder/healthy-flag ambiguity as olanzapine in NCT00245206. |
| 14329 Insulin detemir | M | Both NCT01547169 and NCT01595646 allow MCI **or** AD; NCT01547169 is repeated for two dose arms. |
| 14402 Pitavastatin | D | NCT00548145 requires AD and hypercholesterolemia. |
| 14424 Methylene blue | M | NCT02380573 contains healthy-aging, MCI, and AD cohorts; the drug is assigned in each, so the disease-tagged trial is not wholly AD enrollment. |
| 14475 Semaglutide | M | NCT04777409 and NCT05891496 allow MCI of AD type or mild AD dementia; the enrolled stage cannot be inferred per person from the condition tag. |
| 14539 Prazosin | D | NCT01126099 requires possible/probable AD plus agitation; this is a symptom-treatment study. |
| 14599 Montelukast | M | NCT03991988 explicitly defines separate MCI and early-AD dementia groups; the experimental arm spans them. |
| 14653 Choline | C | Sole source NCT05880849 is a pre-symptomatic, ApoE4-positive risk cohort, not a diagnosed-AD enrollment requirement. |
| 14664 Sapropterin | M | NCT01439555 allows mild AD or MCI, and tetrahydrobiopterin is coadministered with simvastatin and L-arginine. |
| 14685 Progesterone | D | NCT00066157 requires AD in postmenopausal women; medroxyprogesterone is a hormone-therapy arm component, so its effect cannot be isolated by this label alone. |
| 14961 Simvastatin | M | Same MCI-or-AD and three-drug coadministration in NCT01439555. |
| 14962 Trazodone | D | NCT01142258 requires probable AD and targets sleep symptoms. |
| 14968 Modafinil | M | NCT00626210 allows AD or MCI; NCT01172145 requires AD but records healthy flag `true`, an internal registry-field inconsistency. |
| 14975 Sirolimus | M | NCT04200911 allows MCI or AD, despite healthy flag `true`; NCT06022068 likewise allows MCI or dementia of AD type. |
| 14991 Cilostazol | D | NCT01409564 requires probable AD dementia. |
| 14992 Itraconazole | C | Sole source NCT06586606 enrolls healthy participants to test an MK-1708 drug interaction; itraconazole is an interaction perpetrator. |
| 15082 Citalopram | D | NCT00898807 requires probable AD and agitation; symptom target. |
| 15099 Zolpidem | D | NCT03075241 requires probable AD and sleep disturbance; symptom target. |
| 15148 Escitalopram | M | NCT00702780 and NCT01841125 require AD, but NCT01876823 requires depression/cognitive impairment and explicitly excludes probable AD dementia; its AD tag overstates enrollment. |
| 15179 Nicotinamide | M | NCT00580931 requires probable AD; NCT03061474 allows MCI or AD dementia. |
| 15201 Dapagliflozin | D | NCT03801642 requires probable AD. |
| 15284 Interferon beta-1a | D | NCT01075763 requires AD diagnosis. |
| 15308 Riluzole | D | NCT01703117 requires mild AD; the experimental arm label says age-matched cohort but the enrollment criteria are AD-specific. |
| 15331 Insulin aspart | M | NCT02462161 allows AD or MCI; the intranasal arm spans both. |
| 15332 Insulin glulisine | M | NCT01436045 requires probable AD, while NCT02503501 allows amnestic MCI or probable mild AD. |
| 15425 Doxycycline | D | NCT00439166 requires probable AD; doxycycline has combined and single-drug arms. |
| 15611 Suvorexant | D | NCT02750306 requires probable AD and insomnia; symptom target. |
| 15666 Baricitinib | M | NCT05189106 is a basket including subjective cognitive decline, MCI, possible/probable AD, and ALS; not every participant is diagnosed with AD. |
| 15836 Telmisartan | D | NCT02085265 requires probable/possible AD dementia, with possible cerebrovascular disease. |
| 15840 Digoxin | C | Sole source NCT00831506 is a healthy-subject dimebon–digoxin drug-interaction study; two stored entries are arm duplicates. |
| 15986 Salsalate | D | NCT03277573 requires probable AD dementia. |
| 16063 Scopolamine | C | Sole source NCT02051335 enrolls healthy adults; scopolamine induces temporary cognitive deficits as an experimental challenge/probe. |
| 16588 Metformin | M | NCT01965756 allows MCI due to AD or early AD dementia. |
| 16855 Methylphenidate | D | NCT00495820 and NCT01117181 require AD dementia plus apathy; symptom target. |
| 17270 Pimavanserin | D | NCT03118947 is an AD agitation/aggression extension; its own inclusion text relies on prior study completion, while the saved summary identifies probable AD. |
| 18277 Levetiracetam | M | NCT02002819 and NCT03489044 enroll AD; NCT03875638 has both early-AD and healthy-control cohorts, though levetiracetam arms are AD-labeled. |
| 20270 Edaravone | D | NCT05323812 requires early clinical-stage AD criteria; drug is registered as TW001. |

### Parkinson’s: all 39 labels

| Drug ID / name | Audit | Source reason |
|---|:---:|---|
| 14144 Topiramate | D | NCT00794313 requires PD, levodopa use, and dyskinesia; topiramate is combined with amantadine. |
| 14154 Acetaminophen | C | Sole source NCT02305017 is healthy-volunteer opicapone/paracetamol pharmacokinetics; paracetamol is a coadministration probe. |
| 14180 Buspirone | D | NCT02589340 and NCT02803749 require PD; targets include dyskinesia and anxiety. |
| 14189 Nortriptyline | D | NCT00062738 requires PD and depression; symptom target. |
| 14216 Warfarin | C | Both NCT02169440 and NCT02305030 require healthy volunteers and test opicapone/BIA 9-1067 effects on warfarin PK/PD. |
| 14259 Repaglinide | C | Sole source NCT01536366 is a healthy-volunteer BIA 9-1067 pharmacokinetic interaction study. |
| 14286 Rifampicin | C | Sole source NCT04070495 has healthy flag `true`, excludes disease requiring treatment, and uses rifampicin as an interaction perpetrator for KW-6356. |
| 14298 Rosuvastatin | C | Sole source NCT03970798 has healthy flag `true`, excludes disease requiring treatment, and uses rosuvastatin as a KW-6356 interaction substrate. |
| 14299 Sertraline | D | NCT01437189 requires confirmed PD plus major depression; symptom target. |
| 14306 Pioglitazone | D | NCT01280123 requires idiopathic PD. |
| 14318 Ceftriaxone | D | NCT03413384 requires PD dementia. |
| 14406 Mirabegron | D | NCT02536976 requires clinical PD with impaired cognition/overactive bladder; symptom target. |
| 14447 Pitolisant | D | NCT00642928, NCT01036139, and NCT01066442 require PD and daytime sleepiness; four NCT00642928 entries are separate dose arms. |
| 14643 Capsaicin | C | Sole source NCT02183519 includes PD and healthy controls, but capsaicin is nebulized to **provoke reflex cough for measurement**, not given as PD treatment; a challenge/probe role. |
| 14644 Sodium oxybate | D | NCT00641186 and NCT02111122 require PD with sleep disturbance; symptom target. |
| 14656 Cannabidiol | D | NCT02818777 and NCT03582137 require idiopathic PD. |
| 14725 Glycerol phenylbutyrate | M | NCT02046434 enrolls mild PD and normal controls, with blood alpha-synuclein as primary biomarker; it is a mechanistic response study, not patient-only evidence. |
| 14783 Caffeine | C | Sole source NCT03970798 is the healthy-volunteer KW-6356 interaction study; caffeine is an index-substrate probe. |
| 14880 Nicotine | D | NCT00957918 requires probable idiopathic PD and levodopa-induced dyskinesia. |
| 14936 Erythromycin | M | NCT02005029 requires PD, but primary outcomes are gastric emptying and levodopa exposure; the drug is used to alter levodopa absorption, with motor function also examined. Not a healthy-volunteer study, but the disease-level label needs context. |
| 14937 Sildenafil | D | NCT01941732 and NCT02162979 require PD; recorded targets include erectile dysfunction/motor response and dyskinesia. |
| 14956 Carbamazepine | C | Sole source NCT05581823 enrolls healthy adults and uses carbamazepine as CYP3A4 interaction perpetrator to measure tavapadon PK. |
| 14963 Midazolam | C | Sole source NCT03970798 is the healthy-volunteer KW-6356 interaction study; midazolam is an index-substrate probe. |
| 14995 Clarithromycin | C | Sole source NCT04070495 is the healthy-volunteer KW-6356 interaction study; clarithromycin is an interaction perpetrator. |
| 15029 Perampanel | D | NCT00505622, NCT00566462, and NCT01634360 enroll PD patients or PD parent-trial completers; one study is a mechanistic dopamine-imaging pilot. |
| 15099 Zolpidem | D | NCT03621046 requires idiopathic PD. |
| 15116 Paroxetine | D | NCT00062738 requires PD and depression; symptom target. |
| 15126 Donepezil | D | Four NCTs require PD or a PD-parent-study context; measured targets include falls, gait, balance, and dementia. |
| 15201 Dapagliflozin | M | NCT06263673 allows PD **or** Lewy body dementia; registry condition tag does not identify which group received a drug. |
| 15212 Fesoterodine | M | NCT02385500 summary specifies PD with overactive bladder, but its listed inclusion criteria specify bladder symptoms and stable PD medications without an explicit PD diagnostic criterion; symptom/diagnosis details need care. |
| 15426 Isradipine | D | NCT00753636 requires idiopathic PD. |
| 15441 Eszopiclone | D | NCT00324896 requires PD plus insomnia; symptom target. |
| 15496 Rifaximin | M | NCT01662791 and NCT02470780 enroll PD patients, but rifaximin is studied for small-bowel bacterial overgrowth; this is a comorbidity/PD-symptom pathway, not direct evidence of a disease-level PD therapy. |
| 15501 Sitagliptin | M | Same PD-or-Lewy-body-dementia enrollment ambiguity as dapagliflozin in NCT06263673. |
| 15579 Ambroxol | D | NCT05287503 requires idiopathic PD with a GBA1 mutation. |
| 15822 Ursodeoxycholic acid | M | NCT02967250 allows medically stable PD **or healthy controls** and measures brain bioenergetics; PK is a secondary aim, not the sole purpose. |
| 15891 Deferiprone | D | NCT02728843 requires diagnosed PD. |
| 16855 Methylphenidate | D | NCT00359723 and NCT01244269 require PD; NCT01244269 is stored twice for dose arms. |
| 17951 Lixisenatide | D | NCT03439943 requires PD by UK Brain Bank criteria. |

The clear all-supporting concerns are **4/44 Alzheimer’s labels** (choline, itraconazole, digoxin, scopolamine) and **10/39 Parkinson’s labels** (acetaminophen, warfarin, repaglinide, rifampicin, rosuvastatin, capsaicin, caffeine, carbamazepine, midazolam, clarithromycin). The mixed category identifies another **19 Alzheimer’s and 7 Parkinson’s labels** that need source-specific interpretation. These are source-audit counts, not performance metrics for any proposed rule.
