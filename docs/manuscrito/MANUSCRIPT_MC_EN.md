# Manuscript draft, Methods and Concepts (v0.3-en, IEEE T-USON, 26 Nov 2026)

> **Status: internal draft. Not submitted.** Category chosen by the author on 26 Nov 2026: **Methods and Concepts**
> (14 free pages; see `docs/manuscrito/NOTAS_ENVIO_T-USON.md`). This version restructures
> `docs/manuscrito/MANUSCRIPT_DRAFT_EN.md` (v0.2-en) as a protocol paper, with the studies as worked examples. It
> adds no new analysis: every figure cites the results document it comes from; if they disagree, the document
> prevails.
>
> **Still pending before submission:**
>
> - a Scopus or Web of Science search and an external reviewer;
> - authorship, affiliation, funding, competing interests and biographies **[TO BE COMPLETED by the author]**;
> - an English language review;
> - transfer to the official T-USON template.
>
> No affiliation is invented.

---

## Proposed title

**Testing per-case reliability flags for learned ultrasound segmentation: a preregistered, sealed-test protocol with
worked examples in 3D high-frequency mouse embryo imaging**

## Abstract

A segmentation network that measures well on average still fails on some cases, and in practice the reference is not
available to tell which. A per-case reliability flag (green: trust the measurement; yellow or red: do not) addresses
this, but such flags are easy to overrate: thresholds tuned on the evaluation data, test sets reused, failures too few
to show anything, and negative results left unreported.

We describe a protocol for testing such flags. Its core steps are:

1. a tolerance and a failure definition fixed in advance;
2. a flag rule derived from the tolerance, not fitted to data;
3. a domain guard;
4. calibration gates that must be passed before the test set is opened;
5. frozen parameters whose SHA-256 fingerprint is recorded before the test, with code that refuses to run otherwise;
6. a test set opened once;
7. three-state verdicts (supported, not supported, not evaluable or inconclusive);
8. evaluability rules and sample-size planning for the question of whether a flag separates correct from failed
   measurements.

We illustrate each step with a series of preregistered studies on a public 3D high-frequency ultrasound dataset of
mouse embryos. In those studies:

- the gates stopped two flags before they consumed the test set;
- a guard refused to give green where a simulation-calibrated certificate would have given 100% false greens (540 of
  540);
- a stability-based flag passed its gate and, on a sealed test set opened once, failed in 1 of 21 green cases;
- a sample-size simulation exposed a defect in a common rule for declaring "no separation", which we correct.

The protocol, code and all preregistrations are public.

**Index Terms**—Deep learning, high-frequency ultrasound, mouse embryo, preregistration, quality control,
reproducibility, segmentation, uncertainty estimation.

## I. Introduction

Volume and shape measurements from ultrasound increasingly come from learned segmentation. Even accurate networks fail
on some inputs, and the user rarely has a reference to check a given case. A per-case reliability output is therefore
useful: it tells the user when to trust a number.

Disagreement between predictions on transformed inputs is an established estimate of segmentation uncertainty [4], and
it has been used to indicate potential mis-segmentations [5]. Evaluating whether such an estimate can support a
**decision** about a single case is harder than showing that it correlates with error. Common pitfalls are:

- thresholds chosen while looking at the evaluation data;
- the same data used to design and to judge the flag;
- test sets reused after a first look;
- conclusions about whether the flag separates correct from failed cases drawn from a handful of failures;
- failed attempts left out of the report.

This paper documents a protocol that guards against those pitfalls, as a reusable practice rather than a single
result. Section II describes the protocol, Section III works through each step with real studies, and Section IV
discusses what the protocol costs and what it does not solve.

The examples use a public dataset of 3D high-frequency ultrasound volumes of mouse embryos with manual segmentations of
the body and brain ventricles [1]–[3]. No new animal data were generated and no human data were used.

## II. The protocol

### A. Before any data are seen

1. **Fix the tolerance and the failure definition.** Example: a volume measurement fails if it differs from the
   reference by more than τ = 10%. For a small structure, a relative tolerance can be unreachable, and a tolerance in
   boundary voxels (e_b = |V_M − V_R| / A_R ≤ 0.5 voxels) is more appropriate (Section III-D).
2. **Derive the flag rule from the tolerance, not from data.** Example (Section III-C): green if the spread of the
   measured volume across the 8 flips of the image is ≤ τ/2 and the disagreement between the two network stages is ≤ τ.
   Red if either exceeds 2τ or 3τ. Yellow otherwise. With few failures, any fitted threshold learns noise.
3. **Add a domain guard.** It is an envelope of simple image indices (here, an estimated signal-to-noise ratio and the
   edge width, 1–99% percentiles) outside which the flag never gives green. Check that the guard is **computable** on
   the target structure (Section III-D).
4. **Split by subject** (embryo), never by image, into a part for fitting the network, a calibration part and a test
   part.
5. **Write the preregistration:**
   - hypotheses and criteria;
   - minimum numbers for each hypothesis to be evaluable;
   - predictions with probabilities;
   - what each outcome will mean.

   Upload it with the code and its tests before computing anything that decides.

### B. Gates, freezing and the single test

6. **Feasibility gate (G0)** on a few fitting cases: the signals must be computable and the pipeline must reproduce
   the measurement exactly.
7. **Calibration gate** on held-out calibration subjects. Example: at least 10 greens, and at most 10% of them failing.
   If the gate fails, **the test set is not opened**, and a new preregistration is needed.
8. **Freeze and fingerprint.** Write rules, envelope and network hashes to one file, and record its SHA-256 in the
   preregistration before the test. The test command checks the fingerprint, the network hashes and the code
   thresholds, and refuses to run if any differ.
9. **Open the test once.** Afterwards the test set is *used*: no later study may decide with it.
10. **Report three states.** A hypothesis is supported, not supported, or not evaluable or inconclusive. A value that
    cannot be computed is never "not supported".

### C. The separation question

Showing that greens rarely fail is not the same as showing that the flag adds information. With a low base failure
rate, almost any rule that leaves enough greens meets a "greens rarely fail" criterion. The separation question
compares failure rates between non-greens and greens:

- Δ = failure rate among non-greens − failure rate among greens;
- 95% CI by percentile bootstrap, resampling subjects;
- "separates" if the lower bound is > 0;
- "does not separate" if the upper bound is ≤ 5 points;
- otherwise "inconclusive".

We add three rules learned in Section III-E:

- **S-1, evaluability by failures:** require at least 10 failures in total and at least 1 in each group. Otherwise the
  separation hypothesis is not evaluable.
- **S-2, planning:** declare the expected failure rate and aim for about 25 expected failures. With fewer, state in
  advance that "inconclusive" is the likely outcome.
- **S-3:** keep resampling by subject.

### D. Reporting

- Compare the written predictions with the outcomes.
- Record every deviation with its date, approved before the affected quantity is computed.
- Publish negative and non-evaluable studies with the same detail as positive ones.

Table I lists the protocol as a checklist **[to be typeset from Sections II-A to II-D]**.

## III. Worked examples

All studies below follow Section II. Each cites its results document in the public repository.

### A. A domain guard refuses where a simulation-calibrated certificate fails

A certificate calibrated on synthetic data was applied to 1188 real measurements: 180 body and 216 ventricle cases,
each with 3 threshold segmenters. The guard gave no green. Without it, all 540 greens would have been false
[`docs/h11/RESULTADOS_H11.md`]. Recalibrating on simulated ultrasound did not change this: 180 of 180 false greens
without the guard [`docs/h11/RESULTADOS_H12R.md`].

**Lesson (step 3):** the guard is what made the certificate safe on a domain it had never seen.

### B. A calibration gate stops a flag before it consumes the test set

A two-stage network, reimplemented from [1], [3], put 24 of 27 calibration cases within 10% (median Dice 0.938). A
certificate based on image observables then failed the calibration gate: 2 of 16 greens failed, more than giving green
to every case. The test set was not opened [`docs/h19/RESULTADOS_H19.md`].

**Lesson (step 7):** the gate saved the test set for a better candidate.

### C. A stability flag passes and is tested once

The flag of step 2 passed the calibration gate with 12 greens and no failures. After freezing (fingerprint recorded in
the preregistration), the sealed test set (44 cases from 43 embryos) was measured once
[`docs/h20/RESULTADOS_H20.md`]:

| Measure | Value |
|---|---|
| Flags | 21 green, 22 yellow, 1 red |
| Failures among greens (primary) | 1 of 21: 4.8% (CI 0.0–14.3%); supported |
| Failures among non-greens | 2 of 23: 8.7% |
| Difference (non-green − green) | 3.9 points (CI −11.4 to 20.0) |
| Failure rate in all cases | 3 of 44: 6.8% |
| Cases within 10% | 93.2% (median Dice 0.939) |

**Lesson (Section II-C):** the primary criterion was met, but with a 6.8% base failure rate almost any rule would have
met it. The separation interval includes 0. The failing green underestimates volume by 12.9% with both signals low:
the network made the same error on all 8 inputs, which a stability flag cannot see.

### D. Changing the structure exposes the units of the tolerance and a guard defect

The same rule, unchanged, gave no green at all on brain ventricles: 0 of 34 in calibration
[`docs/h23/RESULTADOS_H23.md`].

With the tolerance and signals re-expressed in boundary voxels, the calibration gate still failed: 3 greens of 34. The
guard admitted only 5 of 34 cases, because its indices were not computable for a structure darker than the background
(27 of 34 cases) [`docs/h24/RESULTADOS_H24.md`].

A new preregistration corrected the guard to use the absolute contrast. It then admitted 90% of test cases, against
22.5% for the old guard. The gates passed, and the ventricle test set was opened once (40 cases)
[`docs/h25/RESULTADOS_H25.md`]:

- the network was within 0.5 voxels in 95% of cases;
- the primary hypothesis was not evaluable: 19 greens, where 20 were required;
- separation was inconclusive: 1 of 19 greens and 1 of 21 non-greens failed.

**Lessons (steps 1, 3 and 7):**

- a tolerance must be expressed in units the structure can meet;
- the guard must be checked for computability on each new structure;
- the gates caught both problems without touching the test set.

### E. A sample-size simulation exposes a defect in the "no separation" rule

To plan a future study, we simulated the separation rule of Section II-C
[`docs/h25/TAMANO_MUESTRAL_SEPARACION.md`]:

- **Power:** with about 80 cases and a failure gap like that seen in calibration (5% vs 27%), the rule detects
  separation 83% of the time. A gap of 10 points needs about 270 cases. What matters is the number of failures, not the
  number of cases.
- **A defect:** with no true separation and 40 cases, the rule declared "does not separate" in 35% of simulations. In
  140 of those 144 simulations, there were no failures among non-greens, and the bootstrap interval degenerated.

No published verdict in the series was affected, but a future study could have concluded "no separation" from this
artefact. Rules S-1 to S-3 (Section II-C) prevent it.

## IV. Discussion

**What the protocol buys.**

- Every claim can be traced to a preregistration fixed before the decisive computation.
- No threshold was changed after seeing test data.
- Each sealed test set was opened at most once.
- Two candidate flags were stopped at their gates (Sections III-B and III-D) before they could consume a test set.

**What it costs.**

- Test sets are used up: in this series, both the body and the ventricle test sets are now spent.
- Many studies end as "not evaluable"; half of the studies on real data in this series did.

This is the protocol declining to draw conclusions the data could not support, not a failure of the protocol.

**What it does not solve.**

- A flag based on stability cannot see a consistent error.
- A flag cannot be shown to separate correct from failed measurements without enough failures, which an accurate
  network rarely produces on one dataset.
- The examples come from one public dataset, one system and one species. A direct replication with new volumes is
  preregistered as a base document [`docs/h26/PREREGISTRO_H26_BORRADOR.md`].

**Adapting the protocol.** Steps 1–10 and rules S-1 to S-3 do not depend on the modality or the network. To reuse them,
an author needs:

- a tolerance meaningful for the structure;
- signals available without the reference;
- a guard computable on the target images;
- enough subjects for gates and a single test.

**None of the examples concerns humans or clinical use.**

## V. Data and code availability

- **Data:** public, on IEEE DataPort (doi:10.21227/drmd-xq36, CC BY). Not redistributed.
- **Code, preregistrations, results and the protocol rules** (`docs/REGLAS_PREREGISTRO.md`): in the project repository
  (MIT license), branch `geovida/v0.1-desde-cero`.
- **Reproduction steps:** `docs/REPRODUCCION.md`.

## VI. Declarations

- **Ethics:** only previously published animal data were used; no new animal experiments and no human data.
- **Use of AI:** the code and texts were developed with AI assistance (Claude, Anthropic). The work has not had
  external human scientific review.
- **Funding and competing interests:** **[TO BE COMPLETED by the author]**.

## Figures

Generated by `scripts/figure_manuscript.py` from already-measured cases, with no new analysis.

- **Graphical abstract** (`docs/figures/manuscript_graphical_abstract.png`, 660 × 295 px): the protocol as a flow,
  from the preregistration through the gates and the freezing to a single test, with the examples that stopped at each
  gate.
- **Figure 1** (`docs/figures/manuscript_fig1_lights.png`): error of each test case by flag; A, body (H20); B,
  ventricles (H25). Crosses are failures.
- **Figure 2** (`docs/figures/manuscript_fig2_signals.png`): the two stability signals on the body test set (H20), with
  the rule's thresholds.

## References

References 1, 3, 4 and 5 were checked in PubMed on 26 Nov 2026 (PMID in parentheses).

[1] Qiu Z, Xu T, Langerman J, Das W, Wang C, Nair N, Aristizabal O, Mamou J, Turnbull DH, Ketterling JA, Wang Y. A
   deep learning approach for segmentation, classification, and visualization of 3-D high-frequency ultrasound images
   of mouse embryos. IEEE Trans Ultrason Ferroelectr Freq Control. 2021;68(7):2460–2471.
   doi:10.1109/TUFFC.2021.3068156 (PMID 33755564).
[2] Ultrasound Mouse Embryo Segmentation and Classification [dataset]. IEEE DataPort. doi:10.21227/drmd-xq36. CC BY.
[3] Xu T, Qiu Z, Das W, Wang C, Langerman J, Nair N, Aristizábal O, Mamou J, Turnbull DH, Ketterling JA, Wang Y. Deep
   Mouse: an end-to-end auto-context refinement framework for brain ventricle & body segmentation in embryonic mice
   ultrasound volumes. Proc IEEE Int Symp Biomed Imaging. 2020;2020:122–126. doi:10.1109/isbi45749.2020.9098387
   (PMID 33381278).
[4] Wang G, Li W, Aertsen M, Deprest J, Ourselin S, Vercauteren T. Aleatoric uncertainty estimation with test-time
   augmentation for medical image segmentation with convolutional neural networks. Neurocomputing. 2019;335:34–45.
   doi:10.1016/j.neucom.2019.01.103 (PMID 31595105).
[5] Wang G, Li W, Ourselin S, Vercauteren T. Automatic brain tumor segmentation based on cascaded convolutional neural
   networks with uncertainty estimation. Front Comput Neurosci. 2019;13:56. doi:10.3389/fncom.2019.00056
   (PMID 31456678).
