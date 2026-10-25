# Human checks

Research hypothesis, not medical advice. This tool does not tell anyone what to
take. Talk to a doctor or pharmacist about any medicine.

Things a person should verify by hand, because no automated check in this repository
can establish them. Each item names what to look at, what would count as a problem,
and where the source sits.

## Strict trial-label decisions

Fifteen adjudicated records to check against the frozen rule in
`docs/STRICT_LABEL_RULE.md` (committed at `c041084`, hash `c67af905…b47ae2cd`) —
**10 Alzheimer's and 5 Parkinson's**. Selection is deterministic and rank-blind:
every `uncertain` decision first, then the most judgement-laden exclusions by reason
code (`background_or_coadministered`, `unclear_role`, `no_clinical_objective`,
`interaction_probe`) in record-id order. No ranking position or score took part in
choosing these, and none is shown below.

How to check one: read the eligibility and arm text, then ask the rule's two hard
questions — does the registry **require** the disease diagnosis in the participants
receiving *this* drug, and is *this* drug the intervention under evaluation for a
clinical outcome rather than a probe, tracer, background or co-administered agent?
Condition tags and titles do not count as population evidence. Missing or ambiguous
evidence fails closed. Record agree or disagree and why.

Under `docs/STRICT_LABEL_PROTOCOL.md`, an `uncertain` record is excluded from the
primary strict set and included in the sensitivity analysis, so these are exactly the
records where a human reading could move the headline. Quotes below are verbatim
registry text, truncated; follow the registry link for the full record.


## Alzheimers — 10 decisions to check

### AL-1. Pioglitazone — NCT02284906 (`14306:NCT02284906:pioglitazone`)

- **Adjudicator decision:** `uncertain` — reasons: unclear_population
- **Adjudicator rationale:** The extension requires adjudicated MCI due to AD, but this record does not affirm a biomarker-supported prodromal diagnosis under the frozen Alzheimer gate; AD dementia is expressly excluded.
- **Intervention as registered:** Pioglitazone
- **Title:** AD-4833/TOMM40_303 Extension Study of the Safety and Efficacy of Pioglitazone to Slow Cognitive Decline in Participants With Mild Cognitive Impairment Due to Alzheimer Disease
- **Condition tags:** Mild Cognitive Impairment Due to Alzheimer's Disease
- **Eligibility (verbatim, truncated):** Inclusion Criteria: 1. Completed the pivotal AD-4833/TOMM40\_301 study with an adjudicated diagnosis of mild cognitive impairment (MCI) due to Alzheimer's Disease (AD) without ongoing serious adverse events (SAEs) from AD-4833/TOMM40\_301. 2. Is male or female and is at least 65 years of age at the time of the Baseline Visit. 3. In the opinion of the investigator, is capable of understanding and complying with the protocol requirements. 4. The participant or, when applicable, the participant's legally acceptable representative signs and dates a written, informed consent form and any required p
- **Brief summary (verbatim, truncated):** The purpose of this study is to evaluate the effect of pioglitazone at 24 months compared with placebo on cognitive decline in high-risk participants who have completed the AD-4833/TOMM40\_301 study \[NCT01931566\] with an adjudicated diagnosis of mild cognitive impairment (MCI) due to Alzheimer's Disease (AD).
- **Arms / interventions:**
    - Pioglitazone 0.8 mg / EXPERIMENTAL / Pioglitazone 0.8 mg, tablets, orally, once, daily, for minimum of 2 years.
    - Placebo / PLACEBO_COMPARATOR / Pioglitazone placebo-matching tablets, orally, once, daily, for minimum of 2 years.
    - DRUG: Pioglitazone — Pioglitazone tablets
    - DRUG: Placebo — Pioglitazone placebo-matching tablets
- **Primary outcome:** Change From Extension Study Baseline in Composite Score of a Broad Cognitive Test Battery at Month 24
- **Registry record:** https://clinicaltrials.gov/study/NCT02284906
- **Check:** does the eligibility or arm text *require* the disease diagnosis in the participants receiving this drug, and is this drug the intervention under evaluation for a clinical outcome? Write agree / disagree and why.

### AL-2. Insulin detemir — NCT01547169 (`14329:NCT01547169:insulindetemir`)

- **Adjudicator decision:** `uncertain` — reasons: unclear_population
- **Adjudicator rationale:** The detemir study gives active drug to a pooled MCI/AD population and registers a shared memory endpoint; a separately specified AD clinical outcome is not established.
- **Intervention as registered:** insulin detemir
- **Title:** Study of Nasal Insulin to Fight Forgetfulness - Long-acting Insulin Detemir - 21 Days
- **Condition tags:** Alzheimer's Disease, Mild Cognitive Impairment
- **Eligibility (verbatim, truncated):** Inclusion Criteria: * Age 50-89 * Diagnosed with mild cognitive impairment, or mild/moderate AD Exclusion Criteria: * Excessively high or low blood pressure, heart rate * BMI greater than 34 * Pre-existing diabetes not controlled by exercise * Previous/current use of insulin * Significant elevations in lipids, liver enzymes * Menstrual period within the last 12 months * Significant neurological or medical disorder (other than AD) * Significant use of nasal decongestants * Current use of anti-psychotic, anti-convulsive, anxiolytic, glucocorticoids, or sedative medications
- **Brief summary (verbatim, truncated):** The study will examine the effects of intranasally administered long-acting insulin detemir on cognition in persons with Alzheimer's disease (AD) or amnestic mild cognitive impairment (aMCI). The rationale for these studies is derived from growing evidence that insulin contributes to multiple brain functions, and that insulin dysregulation can contribute to AD pathogenesis. Thus, therapies aimed at restoring normal insulin signaling in the CNS ma
- **Arms / interventions:**
    - Saline / PLACEBO_COMPARATOR
    - Low Dose Insulin Detemir (10IU bid) / EXPERIMENTAL
    - High Dose Insulin Detemir (20IU bid) / EXPERIMENTAL
    - DRUG: Placebo Comparator — saline, taken twice per day for a 3 week duration
- **Primary outcome:** Verbal Memory Composite
- **Registry record:** https://clinicaltrials.gov/study/NCT01547169
- **Check:** does the eligibility or arm text *require* the disease diagnosis in the participants receiving this drug, and is this drug the intervention under evaluation for a clinical outcome? Write agree / disagree and why.

### AL-3. Insulin detemir — NCT01595646 (`14329:NCT01595646:insulindetemir`)

- **Adjudicator decision:** `uncertain` — reasons: unclear_population
- **Adjudicator rationale:** The longer detemir study also pools MCI and AD recipients; memory and daily-function endpoints are not specified separately for AD.
- **Intervention as registered:** Insulin detemir
- **Title:** Study of Nasal Insulin to Fight Forgetfulness - Long-acting Insulin Detemir - 120 Days (SL120)
- **Condition tags:** Alzheimer's Disease, Mild Cognitive Impairment
- **Eligibility (verbatim, truncated):** Inclusion Criteria: * Age 50-89 * Diagnosed with mild cognitive impairment, or mild/moderate AD Exclusion Criteria: * Excessively high or low blood pressure, heart rate * Pre-existing diabetes not controlled by exercise/diet * Previous/current use of insulin * Significant elevations in lipids, liver enzymes * Menstrual period within the last 12 months * Significant neurological or medical disorder (other than AD) * Significant use of nasal decongestants * Current use of anti-psychotic, anti-convulsive, anxiolytic, glucocorticoids, or sedative medications
- **Brief summary (verbatim, truncated):** The study will examine the effects of intranasally administered long-acting insulin detemir on cognition in persons with Alzheimer's disease (AD) or amnestic mild cognitive impairment (aMCI). The rationale for these studies is derived from growing evidence that insulin contributes to multiple brain functions, and that insulin dysregulation can contribute to AD pathogenesis. Thus, therapies aimed at restoring normal insulin signaling in the CNS ma
- **Arms / interventions:**
    - Saline / PLACEBO_COMPARATOR / Saline placebo taken twice per day via intranasal route.
    - Insulin Detemir / EXPERIMENTAL / 20IU of Insulin Detemir taken twice per day (40IU total per day) via intranasal route
    - Insulin / EXPERIMENTAL / 20IU Insulin, administered twice per day (40IU total per day) via intranasal route
    - DRUG: Saline — Saline, administered intranasally twice per day for a 16 week duration
- **Primary outcome:** Verbal Memory Composite
- **Registry record:** https://clinicaltrials.gov/study/NCT01595646
- **Check:** does the eligibility or arm text *require* the disease diagnosis in the participants receiving this drug, and is this drug the intervention under evaluation for a clinical outcome? Write agree / disagree and why.

### AL-4. Montelukast — NCT03991988 (`14599:NCT03991988:montelukast`)

- **Adjudicator decision:** `uncertain` — reasons: unclear_population
- **Adjudicator rationale:** Montelukast has an explicit AD dementia group, but the registered cognitive and behavioral outcomes are not specified separately for that group versus the MCI group.
- **Intervention as registered:** Montelukast
- **Title:** Montelukast Therapy on Alzheimer's Disease
- **Condition tags:** Alzheimer Disease
- **Eligibility (verbatim, truncated):** Inclusion Criteria: 1. Age: 50 years or older 2. MCI group will be defined based on: (i) Subjective memory concern; (ii) Abnormal memory function documented using the Logical Memory subscale (Delayed Paragraph Recall, Paragraph A only) from the Wechsler Memory Scale-Revised (the maximum score is 25): \[\<11 for 16 or more years of education; \<9 for 8-15 years of education; \<6 for \<7 years of education\]; (iii) Montreal Cognitive Assessment (MoCA) \< 26; (iv) Clinical Dementia Rating (CDR) scale /Memory box score=0.5; (v) General functional performance sufficiently preserved (Functional Asse
- **Brief summary (verbatim, truncated):** This is a one-year, double-blind placebo-controlled randomized clinical trial that compares montelukast to placebo in individuals with mild cognitive impairment (MCI) and early Alzheimer's disease (AD) dementia. The measures include cognitive function, cerebrospinal fluid (CSF) biomarkers and neuroimaging (cerebral perfusion and markers of vascular brain damage). Participants will be treated with montelukast (escalating doses:10, 20 to 40 mg) or 
- **Arms / interventions:**
    - Montelukast Group / EXPERIMENTAL / Montelukast (10, 20, or 40 mg)
    - Placebo Group / PLACEBO_COMPARATOR / Matched placebo pill
    - DRUG: Montelukast — Participants in this arm will take a pill of Montelukast daily on escalating doses: 10, 20 to 40 mg. All participants wi
    - DRUG: Placebo oral tablet — Participants in this arm will take a matched placebo pill daily
- **Primary outcome:** Number of Participants With Any Gastrointestinal (GI) Symptoms
- **Registry record:** https://clinicaltrials.gov/study/NCT03991988
- **Check:** does the eligibility or arm text *require* the disease diagnosis in the participants receiving this drug, and is this drug the intervention under evaluation for a clinical outcome? Write agree / disagree and why.

### AL-5. Modafinil — NCT00626210 (`14968:NCT00626210:modafinil`)

- **Adjudicator decision:** `uncertain` — reasons: unclear_population
- **Adjudicator rationale:** Modafinil is tested for sleep/wake disturbance in a pooled AD-or-MCI cohort; the sleep endpoints are not specified separately for diagnosed AD.
- **Intervention as registered:** modafinil
- **Title:** Modafinil Treatment for Sleep/Wake Disturbances in Older Adults
- **Condition tags:** Insomnia, Sleep Initiation and Maintenance Disorders, Alzheimer Disease
- **Eligibility (verbatim, truncated):** Inclusion Criteria: * A clinical diagnosis of Alzheimer's disease or Mild Cognitive Impairment * Subjective complaint of sleep disruption, unsatisfactory sleep, early morning awakening, early bedtime, or excessive daytime sleepiness. Such complaint can be made by either the potential participant or by the caregiver. Exclusion Criteria: * Participation in any other clinical drug trial * Liver failure * Believed by the investigator to be unwilling or unable to follow the protocol * Active liver or coronary disease
- **Brief summary (verbatim, truncated):** Modafinil, trade named Provigil, is a medication approved by the Food and Drug Administration for the treatment of narcolepsy, obstructive sleep apnea/hypopnea syndrome, and shift work sleep disorder. Each of these problems is characterized by difficulty sleeping at night and excessive daytime sleepiness. Modafinil is prescribed during the day to counteract this sleepiness. The idea behind this treatment is that sleepiness that leads to napping d
- **Arms / interventions:**
    - Modafinil / EXPERIMENTAL
    - DRUG: modafinil — 100-400 mg daily for 4 weeks
- **Primary outcome:** Nocturnal Sleep Length at 1 Month
- **Registry record:** https://clinicaltrials.gov/study/NCT00626210
- **Check:** does the eligibility or arm text *require* the disease diagnosis in the participants receiving this drug, and is this drug the intervention under evaluation for a clinical outcome? Write agree / disagree and why.

### AL-6. Sirolimus — NCT04200911 (`14975:NCT04200911:rapamune`)

- **Adjudicator decision:** `uncertain` — reasons: unclear_population
- **Adjudicator rationale:** Rapamune is administered to a pooled MCI/AD cohort. Although cognition and function are listed among exploratory outcomes, AD-specific clinical effects are not separately specified.
- **Intervention as registered:** Rapamune
- **Title:** Cognition, Age, and RaPamycin Effectiveness - DownregulatIon of thE mTor Pathway
- **Condition tags:** Cognitive Impairment, Mild, Alzheimer Disease
- **Eligibility (verbatim, truncated):** Inclusion Criteria: * Diagnosis of Mild Cognitive Impairment (MCI) or Alzheimer's disease, Global Clinical Dementia Rating Scale (CDR)=0.5-1 * Normal blood cell counts without clinically significant excursions; ; normal liver and renal function; and glucose control (HbA1c \< 6.5%). Lipid panel and PT/PTT/INR within normal limits * A Legally Authorized Representative (LAR) if necessary for consent * An LAR or study partner to accompany participant to all visits * Availability for all study visits * Stable dose of AD medications) Donepezil, rivastigmine, memantine, galantamine) for at least 3 mo
- **Brief summary (verbatim, truncated):** Evaluation of central nervous system penetration of orally administered Rapamune (RAPA) in older adults with Mild Cognitive Impairment (MCI) or early Alzheimer's disease (AD) and investigate associated safety, tolerability, target engagement, cognition, and functional status as initial proof-of-concept study
- **Arms / interventions:**
    - RAPA intervention / EXPERIMENTAL / Sirolimus 1mg orally once a day for 8 weeks
    - DRUG: Rapamune — Sirolimus 1mg capsules
- **Primary outcome:** Blood Brain Barrier Penetration of RAPA
- **Registry record:** https://clinicaltrials.gov/study/NCT04200911
- **Check:** does the eligibility or arm text *require* the disease diagnosis in the participants receiving this drug, and is this drug the intervention under evaluation for a clinical outcome? Write agree / disagree and why.

### AL-7. Insulin aspart — NCT02462161 (`15331:NCT02462161:insulinaspart`)

- **Adjudicator decision:** `uncertain` — reasons: unclear_population
- **Adjudicator rationale:** Insulin aspart is tested for cognition in a pooled AD-or-MCI group; no separately specified AD clinical outcome is registered.
- **Intervention as registered:** Insulin aspart
- **Title:** Study of Nasal Insulin to Fight Forgetfulness - Short-Acting Insulin Aspart
- **Condition tags:** Alzheimer's Disease, Mild Cognitive Impairment
- **Eligibility (verbatim, truncated):** Inclusion Criteria: * Previous or subsequent diagnosis of Alzheimer's disease or mild cognitive impairment * Ability to communicate in English Exclusion Criteria: * Preexisting diabetes * Clinically significant elevations in liver function test * Clinically significant elevations in lipid profile * Prior lumbar lumbar surgeries or other medical conditions that render lumbar punctures unsafe * Hemoglobin \<8 g/dl * Significant neurologic disease that might affect cognition, other than Alzheimer's disease, including stroke, Parkinson's disease, multiple sclerosis, or recent severe head injury (w
- **Brief summary (verbatim, truncated):** This pilot clinical trial will examine the effects of intranasal insulin aspart on cognition, daily function, blood and cerebral spinal fluid markers of Alzheimer's disease, and amyloid deposition in the brain. Participants will be randomly assigned to receive insulin aspart or placebo during a 12-week treatment period.
- **Arms / interventions:**
    - Insulin Aspart / EXPERIMENTAL / Fifteen randomly assigned participants with Alzheimer's disease or mild cognitive impairment will receive twice daily intranasal administrat
    - Placebo / PLACEBO_COMPARATOR / Fifteen randomly assigned participants with Alzheimer's disease or mild cognitive impairment will receive twice daily intranasal administrat
    - DRUG: Insulin aspart — Participants will administer 20 IU insulin aspart two times per day with an intranasal delivery device.
    - DRUG: Placebo — Participants will administer placebo two times per day with an intranasal delivery device.
- **Primary outcome:** Change in cognition
- **Registry record:** https://clinicaltrials.gov/study/NCT02462161
- **Check:** does the eligibility or arm text *require* the disease diagnosis in the participants receiving this drug, and is this drug the intervention under evaluation for a clinical outcome? Write agree / disagree and why.

### AL-8. Insulin glulisine — NCT02503501 (`15332:NCT02503501:insulinglulisine`)

- **Adjudicator decision:** `uncertain` — reasons: unclear_population
- **Adjudicator rationale:** Glulisine has a mixed MCI/probable AD population and shared cognitive and function endpoints; no separately specified AD result is registered.
- **Intervention as registered:** Insulin glulisine
- **Title:** Intranasal Glulisine in Amnestic Mild Cognitive Impairment and Probable Mild Alzheimer's Disease
- **Condition tags:** Mild Cognitive Impairment, Alzheimer's Disease (AD)
- **Eligibility (verbatim, truncated):** Inclusion Criteria: Subject is/has * clinical and research diagnosis of amnestic-MCI OR probable mild AD in accordance with National Institute of Neurological and Communicative Disorders and Stroke and the Alzheimer's Disease and Related Disorders Association (NINCDS-ADRDA) criteria * Montreal Cognitive Assessment (MoCA) score 18-27 * Hachinski Ischemia Score \<4 * 50-90 years of age * Females at least 2 years post-menopausal or surgically sterile * Proficiency in speaking, reading and understanding English * Dedicated family member /caregiver, who will be able to attend all visits and report 
- **Brief summary (verbatim, truncated):** This study evaluates the safety and effectiveness of intranasal (IN) glulisine in patients with amnestic mild cognitive impairment (aMCI) and probable Alzheimer's disease. Half of participants will receive IN glulisine, while the other half will receive IN placebo.
- **Arms / interventions:**
    - Insulin Glulisine / EXPERIMENTAL / Insulin Glulisine 20 IU (0.1ml/10 units in each nostril) per intranasal dose, 2 times per day for 6 months
    - Placebo / PLACEBO_COMPARATOR / Saline 20 IU (0.1 ml in each nostril) per intranasal dose, 2 times per day for 6 months
    - DRUG: Insulin glulisine — 
    - DRUG: Placebo — Bacteriostatic 0.9% Sodium Chloride
- **Primary outcome:** Change in Cognition as Measured by the Alzheimer's Disease Assessment Scale - Cognitive 13 (ADAS-Cog 13)
- **Registry record:** https://clinicaltrials.gov/study/NCT02503501
- **Check:** does the eligibility or arm text *require* the disease diagnosis in the participants receiving this drug, and is this drug the intervention under evaluation for a clinical outcome? Write agree / disagree and why.

### AL-9. Sapropterin — NCT01439555 (`14664:NCT01439555:tetrahydrobiopterin`)

- **Adjudicator decision:** `exclude` — reasons: background_or_coadministered
- **Adjudicator rationale:** Sapropterin is given only in an inseparable three-drug regimen; there is no registered component-specific clinical contrast.
- **Intervention as registered:** Tetrahydrobiopterin
- **Title:** Endothelial Facilitation in Alzheimer's Disease
- **Condition tags:** Alzheimer's Disease
- **Eligibility (verbatim, truncated):** Inclusion Criteria: * Subjects must have mild Alzheimer's Disease or Mild Cognitive Impairment (MCI); * age between 55-85; * Mini Mental Status Exam (MMSE) between 15-26; * a caregiver who can provide information, and bring patient to the sessions; * no known allergies to any of the medications to be used; * normal renal function; willingness of patient and spouse/responsible caregiver to participate. Exclusion Criteria: * Significant Psychiatric disorder; * stroke; current use of any of the test medications (e.g., statin, L-Arginine, Kuvan); * phenylketonuria (PKU) ; * elevated serum phenylal
- **Brief summary (verbatim, truncated):** Purpose of the study: Patients with mild Alzheimer's Disease will be given three different drugs over a 4-month period to try to increase the blood flow to their brains, and improve blood vessel and brain function. Each drug can help to open the blood vessels in the brain, and together they may be more effective than each drug alone. The hypothesis is that small blood vessels secrete substances that maintain the integrity of the brain, and may pr
- **Arms / interventions:**
    - Simvastatin + L-Arginine + Tetrahydrobiopterin / EXPERIMENTAL / Simvastatin, 40 mg per day orally; L-Arginine, 2 Gm four times per day orally; Tetrahydrobiopterin 20 mg/kg/day orally
    - DRUG: Simvastatin — Simvastatin, 40 mg per day orally
    - DRUG: L-Arginine — L-Arginine, 2 Gm four times per day orally;
    - DRUG: Tetrahydrobiopterin — Tetrahydrobiopterin 20 mg/kg/day orally
- **Primary outcome:** Mean Change in Cerebral Blood Flow as Measured by Magnetic Resonance Imaging (MRI)
- **Registry record:** https://clinicaltrials.gov/study/NCT01439555
- **Check:** does the eligibility or arm text *require* the disease diagnosis in the participants receiving this drug, and is this drug the intervention under evaluation for a clinical outcome? Write agree / disagree and why.

### AL-10. Simvastatin — NCT01439555 (`14961:NCT01439555:simvastatin`)

- **Adjudicator decision:** `exclude` — reasons: background_or_coadministered
- **Adjudicator rationale:** Simvastatin is one component of the same three-drug regimen, with no registered component-specific clinical contrast.
- **Intervention as registered:** Simvastatin
- **Title:** Endothelial Facilitation in Alzheimer's Disease
- **Condition tags:** Alzheimer's Disease
- **Eligibility (verbatim, truncated):** Inclusion Criteria: * Subjects must have mild Alzheimer's Disease or Mild Cognitive Impairment (MCI); * age between 55-85; * Mini Mental Status Exam (MMSE) between 15-26; * a caregiver who can provide information, and bring patient to the sessions; * no known allergies to any of the medications to be used; * normal renal function; willingness of patient and spouse/responsible caregiver to participate. Exclusion Criteria: * Significant Psychiatric disorder; * stroke; current use of any of the test medications (e.g., statin, L-Arginine, Kuvan); * phenylketonuria (PKU) ; * elevated serum phenylal
- **Brief summary (verbatim, truncated):** Purpose of the study: Patients with mild Alzheimer's Disease will be given three different drugs over a 4-month period to try to increase the blood flow to their brains, and improve blood vessel and brain function. Each drug can help to open the blood vessels in the brain, and together they may be more effective than each drug alone. The hypothesis is that small blood vessels secrete substances that maintain the integrity of the brain, and may pr
- **Arms / interventions:**
    - Simvastatin + L-Arginine + Tetrahydrobiopterin / EXPERIMENTAL / Simvastatin, 40 mg per day orally; L-Arginine, 2 Gm four times per day orally; Tetrahydrobiopterin 20 mg/kg/day orally
    - DRUG: Simvastatin — Simvastatin, 40 mg per day orally
    - DRUG: L-Arginine — L-Arginine, 2 Gm four times per day orally;
    - DRUG: Tetrahydrobiopterin — Tetrahydrobiopterin 20 mg/kg/day orally
- **Primary outcome:** Mean Change in Cerebral Blood Flow as Measured by Magnetic Resonance Imaging (MRI)
- **Registry record:** https://clinicaltrials.gov/study/NCT01439555
- **Check:** does the eligibility or arm text *require* the disease diagnosis in the participants receiving this drug, and is this drug the intervention under evaluation for a clinical outcome? Write agree / disagree and why.


## Parkinsons — 5 decisions to check

### PA-1. Dapagliflozin — NCT06263673 (`15201:NCT06263673:dapagliflozin`)

- **Adjudicator decision:** `uncertain` — reasons: unclear_population
- **Adjudicator rationale:** Dapagliflozin has its own active arm and neurological outcomes, but the eligibility permits Parkinson disease or Lewy body dementia without a separately specified Parkinson treatment cohort and outcomes.
- **Intervention as registered:** Dapagliflozin
- **Title:** Anti-Diabetic Medications to Fight PD and LBD
- **Condition tags:** Lewy Body Dementia, Parkinson Disease
- **Eligibility (verbatim, truncated):** Inclusion Criteria: * Parkinson's disease or Lewy Body Dementia (diagnosis confirmed by neurologist at Mayo Clinic) with stable neurological treatment in the past approximately three months. * Glucose intolerance or mild diabetes: The American Diabetes Association criteria for pre-diabetes/ glucose intolerance includes fasting glucose 100-125, random glucose 140-199, or hemoglobin A1C 5.7-6.4% and diabetes is \> 125 mg/dL, \> 200 mg/dL, and 6.5% or greater, respectively (40). It has been previously reported that 50-80% of individuals with Parkinson's disease have abnormal glucose tolerance (17
- **Brief summary (verbatim, truncated):** The purpose of this study is to test the hypothesis that DPP4 inhibitors and SGLT2 inhibitors are well tolerated and have beneficial neurological effects, specifically for Parkinson's disease and Lewy body dementia.
- **Arms / interventions:**
    - Sitagliptin Group / EXPERIMENTAL / Subjects will receive sitagliptin for the approximately 4-week treatment period.
    - Dapagliflozin Group / EXPERIMENTAL / Subjects will receive dapagliflozin for the approximately 4-week treatment period.
    - Placebo Group / PLACEBO_COMPARATOR / Subjects will receive placebo for the approximately 4-week treatment period.
    - DRUG: Sitagliptin — 100 mg once daily, oral
- **Primary outcome:** Change in Movement Disorder Society- Unified Parkinson's Disease Rating Scale (MDS-UPDRS) Score
- **Registry record:** https://clinicaltrials.gov/study/NCT06263673
- **Check:** does the eligibility or arm text *require* the disease diagnosis in the participants receiving this drug, and is this drug the intervention under evaluation for a clinical outcome? Write agree / disagree and why.

### PA-2. Sitagliptin — NCT06263673 (`15501:NCT06263673:sitagliptin`)

- **Adjudicator decision:** `uncertain` — reasons: unclear_population
- **Adjudicator rationale:** Sitagliptin has its own active arm and neurological outcomes, but the eligibility permits Parkinson disease or Lewy body dementia without a separately specified Parkinson treatment cohort and outcomes.
- **Intervention as registered:** Sitagliptin
- **Title:** Anti-Diabetic Medications to Fight PD and LBD
- **Condition tags:** Lewy Body Dementia, Parkinson Disease
- **Eligibility (verbatim, truncated):** Inclusion Criteria: * Parkinson's disease or Lewy Body Dementia (diagnosis confirmed by neurologist at Mayo Clinic) with stable neurological treatment in the past approximately three months. * Glucose intolerance or mild diabetes: The American Diabetes Association criteria for pre-diabetes/ glucose intolerance includes fasting glucose 100-125, random glucose 140-199, or hemoglobin A1C 5.7-6.4% and diabetes is \> 125 mg/dL, \> 200 mg/dL, and 6.5% or greater, respectively (40). It has been previously reported that 50-80% of individuals with Parkinson's disease have abnormal glucose tolerance (17
- **Brief summary (verbatim, truncated):** The purpose of this study is to test the hypothesis that DPP4 inhibitors and SGLT2 inhibitors are well tolerated and have beneficial neurological effects, specifically for Parkinson's disease and Lewy body dementia.
- **Arms / interventions:**
    - Sitagliptin Group / EXPERIMENTAL / Subjects will receive sitagliptin for the approximately 4-week treatment period.
    - Dapagliflozin Group / EXPERIMENTAL / Subjects will receive dapagliflozin for the approximately 4-week treatment period.
    - Placebo Group / PLACEBO_COMPARATOR / Subjects will receive placebo for the approximately 4-week treatment period.
    - DRUG: Sitagliptin — 100 mg once daily, oral
- **Primary outcome:** Change in Movement Disorder Society- Unified Parkinson's Disease Rating Scale (MDS-UPDRS) Score
- **Registry record:** https://clinicaltrials.gov/study/NCT06263673
- **Check:** does the eligibility or arm text *require* the disease diagnosis in the participants receiving this drug, and is this drug the intervention under evaluation for a clinical outcome? Write agree / disagree and why.

### PA-3. Capsaicin — NCT02183519 (`14643:NCT02183519:capsaicin`)

- **Adjudicator decision:** `exclude` — reasons: no_clinical_objective
- **Adjudicator rationale:** Capsaicin evokes reflex cough as a challenge agent in a physiological comparison; the study does not evaluate its clinical treatment effect.
- **Intervention as registered:** Capsaicin
- **Title:** Respiratory Kinematics of Cough in Healthy Older Adults and Parkinson's Disease
- **Condition tags:** Cough, Parkinson's Disease
- **Eligibility (verbatim, truncated):** Inclusion Criteria: * Age 55-85 years * Ability to provide informed consent For participants with Parkinson's disease (PD): \- Diagnosis of PD (Hoehn \& Yahr stages II-IV) by a University of Florida Movement Disorders fellowship trained neurologist having completed a clinical assessment of each participant's PD severity and arriving at the diagnosis of PD by applying strict United Kingdom brain bank criteria. Exclusion Criteria: Participants with PD: \- History of neurological disorders other than PD (e.g. multiple sclerosis, stroke, brain tumor, etc) Healthy older adults: * History of neurolo
- **Brief summary (verbatim, truncated):** The purpose of this research study is to test cough function in individuals with Parkinson's disease and healthy older adults. Cough is a complex, defensive function which involves movement of the chest and lungs. The investigators want to compare the movement of the chest wall and the lungs during voluntary and reflex cough. The long-term goal of this research is to develop treatments for people with cough dysfunction. Cough dysfunction increase
- **Arms / interventions:**
    - Healthy older adults / EXPERIMENTAL / All participants will receive reflex and voluntary cough testing. This will include coughing on command (voluntary cough) and coughing in re
    - Parkinson's disease / EXPERIMENTAL / All participants will receive reflex and voluntary cough testing. This will include coughing on command (voluntary cough) and coughing in re
    - DRUG: Capsaicin — For reflex cough testing, all participants will receive various concentrations of nebulized capsaicin. Delivery of multi
    - OTHER: Voluntary cough test — Participants will be fitted with a facemask covering their mouth and nose, and instructed to cough into the facemask.
- **Primary outcome:** Peak Expiratory Flow Rate
- **Registry record:** https://clinicaltrials.gov/study/NCT02183519
- **Check:** does the eligibility or arm text *require* the disease diagnosis in the participants receiving this drug, and is this drug the intervention under evaluation for a clinical outcome? Write agree / disagree and why.

### PA-4. Glycerol phenylbutyrate — NCT02046434 (`14725:NCT02046434:glycerolphenylbutyrate`)

- **Adjudicator decision:** `exclude` — reasons: no_clinical_objective
- **Adjudicator rationale:** The phenylbutyrate study measures alpha-synuclein movement into blood; its protocol explicitly expects no symptom effects in this short trial.
- **Intervention as registered:** Glycerol Phenylbutyrate
- **Title:** Phenylbutyrate Response as a Biomarker for Alpha-synuclein Clearance From the Brain
- **Condition tags:** Parkinson's Disease
- **Eligibility (verbatim, truncated):** Inclusion Criteria: * Idiopathic Parkinson's disease with mild symptoms; * May be on treatment with dopamine agonists provided that the treating neurologist agrees: 1. that the drugs can be stopped for at least three weeks prior to participating in the phenylbutyrate study, and 2. for the 4-week duration of the study. * Age and sex matched normal control subjects from spouses and the general population; * In good general health; * Controlled hypertension, or * Controlled hypercholesterolemia with medication. Exclusion Criteria: * Pregnant women; * Current treatment with: 1. L-3,4-dihydroxyphen
- **Brief summary (verbatim, truncated):** This is a Phase I clinical trial of the FDA approved drug Glycerol Phenylbutyrate to see if phenylbutyrate can increase the removal of alpha-synuclein from the brain into the bloodstream. Alpha-synuclein forms abnormal protein deposits in dopamine neurons and is believed to cause the death of brain cells, leading to Parkinson's Disease.
- **Arms / interventions:**
    - Parkinson's Diesase / EXPERIMENTAL / Participant will take Glycerol Phenylbutyrate, participant has Parkinson's Disease
    - Control / EXPERIMENTAL / Participant does not have Parkinson's Disease, Participant will be taking glycerol phenylbutyrate
    - DRUG: Glycerol Phenylbutyrate — 
- **Primary outcome:** Levels of alpha-synuclein in blood plasma
- **Registry record:** https://clinicaltrials.gov/study/NCT02046434
- **Check:** does the eligibility or arm text *require* the disease diagnosis in the participants receiving this drug, and is this drug the intervention under evaluation for a clinical outcome? Write agree / disagree and why.

### PA-5. Perampanel — NCT00566462 (`15029:NCT00566462:perampanel`)

- **Adjudicator decision:** `exclude` — reasons: no_clinical_objective
- **Adjudicator rationale:** This perampanel study measures striatal imaging binding after a levodopa challenge and specifies no disease-relevant clinical objective or outcome.
- **Intervention as registered:** perampanel
- **Title:** Assessment of Perampanel (E2007) on Synaptic Dopamine in Mild-moderate PD Patients: A Pilot Study With [^123I]-IBZM SPECT
- **Condition tags:** Parkinson's Disease
- **Eligibility (verbatim, truncated):** INCLUSION CRITERIA: 1. Male or female patients with idiopathic PD fulfilling the United Kingdom Parkinson's Disease Society Brain Bank (UKPDSBB) diagnostic criteria, with a good response to levodopa. The requirement in the UKPDSBB Step 2 for prior brain imaging is at the discretion of the investigator. * Clinical diagnosis of idiopathic Parkinson's disease (patients must have at least two of the three cardinal symptoms: resting tremor, rigidity, bradykinesia) * Hoehn and Yahr Stage II to IV. * Treatment with monotherapy of levodopa plus an aromatic acid decarboxylase inhibitor (carbidopa). The
- **Brief summary (verbatim, truncated):** This is a two-arm, double-blind, placebo-controlled study.
- **Arms / interventions:**
    - perampanel / EXPERIMENTAL
    - 1 / PLACEBO_COMPARATOR
    - DRUG: perampanel — 2 mg/d for 14 days followed by 4 mg/d for 14 days
    - DRUG: placebo — Matching placebo for for 14 days followed by 4 mg/d for 14 days
- **Primary outcome:** Change in Striatal [^123I]-Iodobenzamine (IBZM_ Binding Following a Single Dose Carbidopa/Levodopa Challenge for 15-hours at Baseline and Week 4
- **Registry record:** https://clinicaltrials.gov/study/NCT00566462
- **Check:** does the eligibility or arm text *require* the disease diagnosis in the participants receiving this drug, and is this drug the intervention under evaluation for a clinical outcome? Write agree / disagree and why.


## Other things only a person can confirm

- **The three families tagged "human evidence in Alzheimer's"** on the gap map: read
  the quote on each card and confirm the trial really was in an Alzheimer's cohort.
  The tag is a keyword heuristic over the verbatim quote and under-claims by design.
- **The four verdict disagreements** listed in `docs/METHODOLOGY.md`: Mecasermin and
  Cerliponase alfa (human evidence for a different disease), Pegaptanib (a harm
  signal read as support), Teprotumumab (a label that does not fit its evidence).
- **Any claim shown as supported**: the span checker proves the quote appears in the
  cited abstract. It cannot prove the quote supports the sentence built around it.
- **The demo script's spoken numbers** against `artifacts/headline_numbers.json`.
