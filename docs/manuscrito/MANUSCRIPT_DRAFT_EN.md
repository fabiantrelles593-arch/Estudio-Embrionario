# Manuscript draft (v0.2-en, IEEE T-USON format, 26 Nov 2026)

> **Status: internal draft. Not submitted to any journal.** English version of
> `docs/manuscrito/BORRADOR_MANUSCRITO.md`, adapted to IEEE Transactions on Ultrasonics (T-USON): Index Terms,
> numbered IEEE references and a contributions paragraph (`docs/manuscrito/NOTAS_ENVIO_T-USON.md`). If a figure
> disagrees with the cited results documents, those documents prevail. Before submission, per §6 of `docs/SINTESIS_CERTIFICADO.md`:
>
> 1. a Scopus or Web of Science search and a second reviewer;
> 2. review by an external advisor;
> 3. the author's decisions on authorship, affiliation and journal.
>
> Every figure comes from a results document on the branch, cited in square brackets. No new analysis.
>
> Authors and affiliation: **[TO BE COMPLETED by the author]**. No affiliation is invented.

---

## Proposed title

**A per-case reliability flag based on the network's own stability for embryo volume measurement in 3D
high-frequency ultrasound: a preregistered evaluation with a sealed test set**

## Abstract

**Objective.** To determine whether an instrument can tell, case by case and without the reference, when its volume
measurement of a mouse embryo in 3D ultrasound is reliable (within 10% of the manual reference).

**Methods.** We used a public dataset of 3D high-frequency ultrasound (HFU) volumes of mouse embryos with manual
segmentations [1], [2]. Every study was preregistered before computing the quantity that decided it. Sealed
test sets were opened only once, after the SHA-256 fingerprint of the frozen parameters had been recorded. We compared
three sources of reliability:

- a certificate calibrated on simulated data;
- a certificate based on image observables, on top of a two-stage segmentation network;
- a flag based only on that network's stability under the 8 flips of the image and on the agreement between its two
  stages, with thresholds derived from the tolerance and not fitted to the data.

**Results.**

- Without a domain guard, the simulation-calibrated certificate gave 100% false greens on real data (540 of 540). With
  the guard, it refused to give green.
- The image-observable certificate failed its calibration gate: 2 of 16 greens failed.
- The stability flag passed calibration. On the sealed test set (44 cases, 43 unseen embryos), 1 of 21 greens failed:
  4.8%, 95% CI 0.0–14.3%.
- The network measured 93.2% of unseen embryos within 10% (median Dice 0.939).
- The flag did not show that it separates correct from failed measurements: the failure rate among non-greens minus
  that among greens was 3.9 points, CI −11.4 to 20.0.
- For brain ventricles, with the tolerance expressed in boundary voxels, the network was within 0.5 voxels in 95% of
  40 unseen cases. With 2 failures, neither primary hypothesis could be answered.

**Conclusion.** The network's own stability gave a safe green flag for body volume in unseen embryos from one dataset.
Whether it separates correct from failed measurements remains unshown, because the network rarely fails on these data.
A second dataset is needed, with more failures or many more cases.

**Index Terms**—Deep learning, high-frequency ultrasound, mouse embryo, preregistration, quality control, segmentation,
uncertainty estimation.

## 1. Introduction

Measuring embryo volume in 3D ultrasound requires segmentation. No segmenter is always right, and in practice the
reference is not available to tell whether a given case was measured well. A useful measurement should come with a
per-case indication of whether it can be trusted.

Using the disagreement between predictions on transformed inputs as a measure of segmentation uncertainty has been
published [4], as has its use to flag erroneous segmentations in cascaded networks [5]. Here we test it on 3D HFU of mouse embryos under three less common conditions:

1. a fixed rule, with thresholds derived from the tolerance and not fitted to the data;
2. calibration gates that must be passed before the test set is opened;
3. a sealed test set, opened only once after the parameters were frozen and fingerprinted.

We also report the negative results that led to this rule.

**Contributions and difference from prior work.** Earlier work on test-time augmentation estimated voxel- and
structure-level uncertainty in brain MRI and showed that it can indicate potential mis-segmentations [4], [5]. The
work that produced this dataset reported segmentation accuracy, not per-case reliability [1], [3]. Here:

1. the reliability output is a per-case decision (green, yellow or red) with a fixed rule and a declared tolerance;
2. its safety is tested on a sealed test set, opened once after freezing;
3. it is compared, on the same data, with a simulation-calibrated certificate and with image observables, and the
   failures of those alternatives are reported;
4. the question it does not answer (separating correct from failed measurements) is stated, with the sample size
   needed to answer it.

Our literature search covered PubMed and Europe PMC; a Scopus or Web of Science search is still pending, so we do not
claim this is the first such evaluation.

## 2. Methods

### 2.1. Data

Public dataset of 3D HFU volumes of mouse embryos with manual segmentation of the body and the brain ventricles
[1], [2] (IEEE DataPort, doi:10.21227/drmd-xq36; CC BY license). The public archive contains 180 body cases and
216 ventricle cases [`docs/h11/RESULTADOS_H11.md`]. No new animal data were generated and no human data were used.

**Split.** We used the dataset authors' train/test split, by embryo: no embryo appears on both sides. Training
embryos were divided, with a fixed seed, into network fitting (109 cases) and certificate calibration (27 cases). The
body test set has 44 cases from 43 embryos [`docs/h20/PREREGISTRO_H20.md` §3].

### 2.2. Segmentation network

An independent reimplementation, from the publications, of the two-stage idea of [3] and [1]; no code or weights were copied. Stage 1 is a small 3D U-Net at ¼ resolution over the whole volume. Stage 2
works at ½ resolution in a box around the stage-1 result, with its probability as a second channel. It was trained on
CPU with random flips along the three axes. The measurement is the volume of the full-resolution mask, keeping the
largest connected component [`src/geovida/h19.py`].

### 2.3. Signals and flag rule

With V_k the volume obtained with the k-th of the 8 flips (V_0, the image as is, is the measurement) and V_c the
volume from stage 1 alone:

- s_flip = (max V_k − min V_k) / V_0;
- s_stage = |V_c − V_0| / V_0.

With tolerance τ = 10%, the flag is:

- **green** if the case is inside the domain, s_flip ≤ τ/2 and s_stage ≤ τ;
- **red** if s_flip > 2τ or s_stage > 3τ;
- **yellow** otherwise.

The thresholds were fixed before any signal was computed [`docs/h20/PREREGISTRO_H20.md` §4].

**Domain guard.** A 1–99% percentile envelope of two image indices (estimated signal-to-noise ratio and edge width),
fitted on the calibration set.

### 2.4. Protocol

Each study was preregistered with:

- its hypotheses;
- its criteria;
- its minimum sample sizes for evaluability;
- its predictions with probabilities.

The preregistration was uploaded with the code and its tests before anything was computed. The order was fixed:
feasibility (G0), calibration gate, freezing of the parameters with their SHA-256 fingerprint recorded in the
preregistration and, only then, the test. The program refused to open the test set if the fingerprint did not match.

**Primary criterion (body).** Fraction of greens with |volume error| > 10%. Supported if the estimate is ≤ 10%;
evaluable with at least 20 greens from at least 15 embryos.

**Statistics.** 95% CIs by percentile bootstrap, resampling embryos (2000 replicates).

## 3. Results

### 3.1. A simulation-calibrated certificate does not transfer to real data

The certificate calibrated on synthetic data was applied to 1188 real measurements: 180 body cases and 216 ventricle
cases, each with 3 threshold segmenters. The domain guard gave no green. Without the guard, all 540 greens would have
been false [`docs/h11/RESULTADOS_H11.md`]. Recalibrated on simulated ultrasound, the result was the same (180 of 180
false greens without the guard) [`docs/h11/RESULTADOS_H12R.md`].

### 3.2. The network measures well, but image observables do not anticipate its failures

With threshold segmenters, even with clean-up, only 1 of 136 training cases was within 10%
[`docs/h18/RESULTADOS_H18.md`]. The two-stage network put 24 of 27 calibration cases within 10% (median Dice 0.938).
Its image-observable certificate failed the calibration gate: 2 of 16 greens failed, more than giving green to every
case [`docs/h19/RESULTADOS_H19.md`].

### 3.3. The stability flag on the sealed test set

It passed the calibration gate with 12 greens and no failures. On the test set (44 cases from 43 embryos, opened once)
[`docs/h20/RESULTADOS_H20.md`]:

| Measure | Value |
|---|---|
| Flags | 21 green (47.7%), 22 yellow, 1 red |
| Failures among greens (primary) | 1 of 21: 4.8% (CI 0.0–14.3%); **supported** |
| Failures among non-greens | 2 of 23: 8.7% |
| Difference (non-green − green) | 3.9 points (CI −11.4 to 20.0) |
| Failure rate in all cases | 3 of 44: 6.8% |
| Cases within 10% / within 5% | 93.2% / 75.0% |
| Median Dice | 0.939 |

The failing green underestimates volume by 12.9% with both signals low: the network makes the same error on all 8
inputs.

### 3.4. Brain ventricles

The same rule, unchanged, gave no green for ventricles [`docs/h23/RESULTADOS_H23.md`]. With the tolerance and signals
expressed in boundary voxels, the limiting factor became the domain guard, which could not measure a structure darker
than the background [`docs/h24/RESULTADOS_H24.md`]. With the guard corrected, on the ventricle test set (40 cases from
40 embryos, opened once) [`docs/h25/RESULTADOS_H25.md`]:

- the network was within 0.5 voxels of the reference in 95% of cases (median Dice 0.890);
- there were 19 greens, 1 of which failed; the primary hypothesis was not evaluable, because 20 were required;
- separation was inconclusive: 1 of 19 greens and 1 of 21 non-greens failed, a difference of −0.5 points (CI −15.0 to
  13.0).

## 4. Discussion

**What holds.** In one public mouse-embryo dataset, a green flag given only by the network's stability was right on
unseen embryos, in a sealed test measured once. Image observables did not achieve this with the same network. A
simulation-calibrated certificate without a domain guard would have given false greens in every case.

**The main limitation.** With a 6.8% failure rate on the test set, almost any rule that left enough greens would have
met the primary criterion. The result mainly says that the network is accurate on this dataset. That the flag
separates correct from failed measurements is not shown, for body or ventricles. A sample-size simulation shows that
answering it requires on the order of 10 to 25 failures [`docs/h25/TAMANO_MUESTRAL_SEPARACION.md`].

**What the flag cannot see.** An error the network makes identically on every input produces no instability. The only
failing green on the test set is of this kind.

**Other limitations.**

- The reference is a human contour: we measure agreement, not truth.
- All real data come from one dataset, one system and one species.
- The thresholds are judgments fixed in advance; they were not compared with alternatives.

**Next step.** A direct replication with new volumes and the frozen instrument. It is already preregistered as a base
document, with a minimum number of failures for assessing separation [`docs/h26/PREREGISTRO_H26_BORRADOR.md`].

**None of this concerns humans or clinical use.**

## 5. Data and code availability

- **Data:** public, on IEEE DataPort (doi:10.21227/drmd-xq36, CC BY). Not redistributed.
- **Code, preregistrations and results:** in the project repository (MIT license), branch `geovida/v0.1-desde-cero`.
- **Reproduction:** `docs/REPRODUCCION.md`.

## 6. Declarations

- **Ethics:** only previously published animal data were used; the study generated no new animal data and used no
  human data.
- **Use of AI:** the code and texts were developed with AI assistance (Claude, Anthropic). The work has not had
  external human scientific review.
- **Funding and competing interests:** **[TO BE COMPLETED by the author]**.

## Figures

Generated by `scripts/figure_manuscript.py` from the already-measured test cases of H20 and H25, with no new analysis.
The script first checks that the counts match the published ones. The images (`docs/figures/manuscript_fig1_lights.png`
and `docs/figures/manuscript_fig2_signals.png`) are created when it runs.

**Figure 1. Error of each test case by flag.**

- **A. Body, H20 sealed test (44 cases):** |volume error| in %; the dashed line marks the 10% tolerance.
- **B. Ventricles, H25 test (40 cases):** boundary error e_b in voxels; the tolerance is 0.5 voxels.

Crosses are failures. In A, 1 of the 21 greens fails: it underestimates volume by 12.9% with both signals low. In B,
the failing green is just above the limit (0.51), and the gross failure (2.34) is yellow.

**Figure 2. The two stability signals on the body test set (H20).** Dashed lines mark the rule's thresholds: τ/2 and
2τ for s_flip, and τ for s_stage. Yellows inside the green region are outside the domain according to the guard. The
three crosses are the failures: neither signal clearly separates them from correct measurements, which is what H20d
could not show.

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
