#!/usr/bin/env python
"""What an approach physically requires: instruments, the physics that forces them, cost, people.

WHY THIS LAYER EXISTS. The barriers tab says why a disease is hard. It still reads as if the
fix were a matter of will. It is not — it is a matter of a room, a machine, a physical limit,
and a payroll. A researcher who reads "in vivo base editing" and does not know that measuring
the result at 0.5% allele fraction needs droplet partitioning, or that the vector needs a
full/empty capsid ratio only an analytical ultracentrifuge can give, has a plan with a hole in
it exactly where the money is.

THE PHYSICS FIELD IS THE POINT. Every instrument here carries the reason the measurement
CANNOT be made another way — a scattering cross-section, a seal resistance, a signal-to-noise
scaling, a sedimentation coefficient. Where a cheaper instrument would do, that is said too,
in its own field, because a capability list that only ever goes up is a shopping list rather
than a plan.

WHAT THE COSTS ARE AND ARE NOT. Capital figures are order-of-magnitude list prices for a new
instrument, in 2025-2026 US dollars, as a BAND — never a point, because list price is not
transaction price and academic, consortium and trade-in discounts routinely move it by 20-40%.
Operating cost is the annual service contract plus consumables at a normal duty cycle; service
alone is conventionally 8-12% of capital per year, which is why a donated instrument is not a
free instrument. Siting — floor loading, shielding, chilled water, a quiet room — is carried
separately, because for the largest instruments it exceeds the instrument.

STAFF IS IN FTE, not headcount, and names the specialism, because the scarce input in a rare
disease programme is usually not the machine. A cryo-EM at a site with nobody who can process
the data is a very expensive cold room.

PROVENANCE. Written from working knowledge of instrumentation and of published programmes. The
physics is textbook and checkable. The cost bands are engineering estimates and should be
treated as such: right to about a factor of two, not to a decimal. Nothing here is a
procurement quote, and nothing here is clinical guidance.

    python tools/capability_seed.py     # writes out/rare/capability.json
"""

from __future__ import annotations

import json
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / "out" / "rare"


def inst(id, name, klass, physics, measures, limit, capex, opex, siting, fte, roles, cheaper=None):
    return dict(id=id, name=name, klass=klass, physics=physics, measures=measures, limit=limit,
                capexUSD=list(capex), opexUSDyr=opex, sitingUSD=siting, fte=fte, roles=roles,
                cheaperRoute=cheaper)


# --- the instruments, and the physics that forces each one ---------------------------
INSTRUMENTS = [
    inst("nanopore", "Long-read sequencer (nanopore, production scale)", "sequencing",
         "A single strand is pulled through a protein pore under an applied potential; each "
         "base in the constriction blocks the ionic current by a characteristic amount. Because "
         "the read is one continuous translocation, read length is limited by the molecule you "
         "loaded and not by the chemistry — so a 4 kb inversion is spanned by ONE read. Short "
         "reads cannot do this at any depth: a 150 bp read has no way to be inside a breakpoint "
         "and outside it at the same time.",
         "Structural variants, repeat expansions, phasing, and 5-methylcytosine read directly "
         "from the current deviation — no bisulfite conversion, therefore no conversion damage.",
         "Single-read accuracy about 99%; structural variants down to ~50 bp at 20x. Methylation "
         "calls are ~95% accurate per CpG, which is why X-inactivation skew needs depth rather "
         "than one good read.",
         (180_000, 260_000), 90_000, 15_000, 1.5,
         ["Sequencing technologist 1.0", "Bioinformatician, SV and methylation 0.5"],
         "A single flow-cell handheld device is about $1,000 and answers a one-family question. "
         "The production instrument is only justified past roughly 200 samples a year."),

    inst("illumina", "Short-read sequencer, mid-throughput", "sequencing",
         "Sequencing by synthesis: a fluorescent, reversibly terminated base is imaged on a "
         "clonal cluster, cycle by cycle. Accuracy comes from averaging over a clonal "
         "population — which is exactly why the read is short. The clusters dephase, and "
         "signal-to-noise collapses after a few hundred cycles.",
         "Point variants and small indels at the lowest cost per base available; the workhorse "
         "of exome and panel diagnosis.",
         "Q30 at 2x150 bp. Blind to balanced rearrangements and to expansions longer than the "
         "insert — the failure mode that leaves a patient undiagnosed after a normal exome.",
         (300_000, 400_000), 45_000, 10_000, 1.0,
         ["Sequencing technologist 0.7", "Variant analyst 0.3"],
         "A core facility sells an exome for $300-900 and needs no capital at all. Owning the "
         "instrument is a throughput decision, not a capability one."),

    inst("optical_map", "Optical genome mapping", "genomics",
         "Long DNA molecules are fluorescently labelled at a specific 6-mer motif and stretched "
         "single-file through nanochannels narrow enough to stop them coiling. The instrument "
         "measures the DISTANCE between labels over megabases. It never reads a base — it reads "
         "geometry, which is why it sees a 100 kb inversion that an assembly walks straight "
         "through.",
         "Large structural variants, balanced translocations, and the deletion and duplication "
         "breakpoints that dominate Duchenne genotypes.",
         "Sensitive from about 500 bp insertions up to whole-arm events; cannot call a point "
         "variant at all. It complements sequencing and never replaces it.",
         (300_000, 400_000), 55_000, 5_000, 1.0,
         ["Genomics technologist 0.7", "Cytogeneticist 0.3"],
         "Karyotype plus MLPA covers the common Duchenne deletions for a few hundred dollars. "
         "Optical mapping earns its place on the roughly 7% of patients those miss."),

    inst("ddpcr", "Droplet digital PCR", "molecular",
         "The reaction is partitioned into about 20,000 nanolitre droplets before amplification. "
         "Each droplet ends positive or negative, and the starting concentration follows from "
         "the Poisson statistics of the empty ones. There is no standard curve and no "
         "amplification-efficiency assumption — which is the entire reason it can call a 0.3% "
         "edited allele fraction that qPCR cannot separate from its own noise floor.",
         "Absolute copy number: editing efficiency, vector genome titre, transgene copies per "
         "diploid genome, circulating cell-free DNA.",
         "Down to about 0.1% allele fraction with enough input. The limit is how many genome "
         "equivalents you can physically load, not the instrument.",
         (100_000, 150_000), 40_000, 0, 0.5,
         ["Molecular technologist 0.5"],
         "None that keeps absolute quantification. qPCR costs a tenth and answers a weaker "
         "question — relative, and against an assumption."),

    inst("patch", "Automated planar patch clamp", "electrophysiology",
         "A cell is drawn by suction onto a micrometre aperture until the seal between membrane "
         "and substrate exceeds one gigaohm. That seal resistance IS the experiment: below it, "
         "leak current through the gap swamps the picoampere currents through the channel. "
         "Automation runs hundreds of apertures in parallel, which is what turns a "
         "variant-by-variant question into a screen.",
         "Whether a given SCN1A or KCNQ2 variant is loss- or gain-of-function — the distinction "
         "that decides whether a sodium-channel blocker helps a patient or harms them.",
         "Whole-cell currents to a few picoamperes. It cannot see single-channel events and it "
         "cannot see a network; for the network you need the array below.",
         (500_000, 900_000), 110_000, 20_000, 1.5,
         ["Electrophysiologist 1.0", "Cell culture technologist 0.5"],
         "A manual rig costs $80-150k and gives better data per cell at perhaps 1% of the "
         "throughput. For an n-of-1 variant question the manual rig is the correct purchase."),

    inst("mea", "Multi-electrode array", "electrophysiology",
         "Extracellular electrodes beneath a cultured network record the field potential the "
         "cells themselves generate. No seal is formed, so nothing is broken and the same "
         "culture can be recorded for weeks. The price of that is what you measure: the "
         "network's firing, never the current through one channel.",
         "Network phenotype in patient iPSC-derived neurons — burst rate, synchrony, and whether "
         "a candidate compound moves them toward the control network.",
         "Spikes and bursts only; nothing subthreshold. A drug that fixes the channel but not "
         "the network reads as a failure here, and sometimes that reading is correct.",
         (60_000, 120_000), 25_000, 0, 1.0,
         ["Stem-cell technologist 0.7", "Data analyst 0.3"], None),

    inst("lcms", "LC-MS/MS, triple quadrupole", "analytical",
         "The first quadrupole selects a precursor ion by mass-to-charge, a collision cell "
         "fragments it, and the third selects one fragment. Requiring BOTH masses is what buys "
         "selectivity in plasma, where the analyte sits in a matrix millions of times more "
         "abundant than itself. The chromatography in front separates isobars that no mass "
         "filter can.",
         "Very-long-chain fatty acids for peroxisomal disease, homogentisic acid for "
         "alkaptonuria, plasmalogens, and pharmacokinetics of anything dosed.",
         "Low nanomolar to picomolar in plasma for a validated transition — but quantitative "
         "only against an isotope-labelled internal standard. Buying the instrument without the "
         "standards buys a very precise relative number.",
         (250_000, 400_000), 60_000, 15_000, 1.5,
         ["Analytical chemist 1.0", "Sample preparation technologist 0.5"], None),

    inst("confocal", "Spinning-disk confocal with environmental control", "imaging",
         "A pinhole rejects light originating outside the focal plane, so a thick living sample "
         "is sectioned optically instead of physically. Spinning a disk of pinholes spreads the "
         "excitation over many of them at once: identical sectioning at a fraction of the dose, "
         "which is the only reason the organoid is still alive at the end of the time course.",
         "Forskolin-induced swelling in patient-derived intestinal organoids — CFTR theratyping, "
         "read out as change in cross-sectional area over an hour.",
         "About 250 nm laterally. Photobleaching, not resolution, sets how long you may watch.",
         (400_000, 700_000), 70_000, 25_000, 1.5,
         ["Imaging specialist 0.7", "Organoid culture technologist 0.8"],
         "For swelling alone, a good widefield with a stage-top incubator does the job at a "
         "quarter of the price. Confocal buys the harder assays that come afterwards."),

    inst("highcontent", "High-content imaging screen", "imaging",
         "A confocal with a plate handler and an analysis pipeline, so the unit of measurement "
         "becomes the plate rather than the field of view. Physically nothing new is bought — "
         "what is bought is throughput, and the statistics that follow from it.",
         "Compound and guide-RNA screens read out as cell morphology across tens of thousands "
         "of wells.",
         "At this scale batch and edge effects dominate. A screen without plate-position "
         "randomisation measures the plate, and does so very precisely.",
         (700_000, 1_100_000), 120_000, 30_000, 2.5,
         ["Screening scientist 1.0", "Automation engineer 0.5", "Image analyst 1.0"], None),

    inst("sorter", "Fluorescence-activated cell sorter", "cell",
         "Cells cross a laser in single file; scattered and emitted light is measured, the "
         "stream is broken into charged droplets, and deflection plates throw each droplet left "
         "or right. The method rests entirely on the droplet holding exactly one cell, which is "
         "why sorting faster than roughly 30,000 events per second costs purity rather than "
         "saving time.",
         "Separating edited from unedited cells, isolating rare progenitors, immune subsets.",
         "Four to five decades of dynamic range per channel. Aerosol containment is mandatory "
         "for patient material and is a real line in the budget.",
         (400_000, 650_000), 80_000, 40_000, 1.0,
         ["Flow cytometry specialist 1.0"], None),

    inst("auc", "Analytical ultracentrifuge", "biophysics",
         "The sample is spun at up to 60,000 rpm while its concentration profile is watched "
         "optically in real time. A DNA-filled AAV capsid and an empty one are nearly the same "
         "size and very different densities, so they sediment at measurably different rates. "
         "This is a first-principles measurement of the full-to-empty ratio: no standard, no "
         "calibration curve, no assumption.",
         "Full versus empty capsid fraction in a vector lot, and aggregation state.",
         "Resolves capsid species differing by a few percent in sedimentation coefficient. It "
         "is slow — a run is hours — so it releases a lot, it does not screen one.",
         (400_000, 600_000), 55_000, 10_000, 0.5,
         ["Biophysicist 0.5"],
         "Charge-detection mass spectrometry is faster and comparably informative. Empty capsids "
         "that get dosed are pure immunogen, so SOME orthogonal measurement is not optional."),

    inst("bioreactor", "Single-use bioreactor suite, 50-200 L", "manufacture",
         "Suspension culture in a disposable bag under controlled gas transfer, pH and shear. "
         "Scale-up is bounded by oxygen transfer per unit volume and by the shear the cells "
         "tolerate — which is why you cannot simply use a larger vessel, and why an adherent "
         "process hits a wall that a suspension process does not.",
         "Producing viral vector at the dose a systemic administration actually requires.",
         "A systemic AAV dose of 1e14 vector genomes per kilogram, given to a 20 kg child, is "
         "2e15 genomes for ONE patient. That number is the AAV ceiling, written as a volume.",
         (1_500_000, 3_000_000), 400_000, 500_000, 6.0,
         ["Process engineer 2.0", "Manufacturing technologist 3.0", "QC analyst 1.0"], None),

    inst("cleanroom", "GMP cleanroom suite, grade B/C", "facility",
         "Classification is a particle count under HEPA filtration at a specified air-change "
         "rate, held under a positive pressure cascade. The cost is not the room. It is the "
         "validated environmental monitoring, the qualified people, and the documentation that "
         "makes a batch releasable rather than merely clean.",
         "The regulatory gate between a construct that works and a dose that may be given.",
         "This is the real wall in front of one-patient therapies: the dossier is the same size "
         "for a cohort of 1 and a cohort of 10,000. It is the economic barrier, as a building.",
         (10_000_000, 22_000_000), 2_500_000, 0, 12.0,
         ["QA 3.0", "Qualified person and QC 3.0", "Manufacturing 5.0", "Facilities 1.0"],
         "A hospital-exemption or shared academic GMP unit spreads the burden across programmes. "
         "It is the only route that makes an n-of-1 antisense drug arithmetically possible."),

    inst("mri3t", "3 T MRI", "clinical imaging",
         "Signal-to-noise rises roughly linearly with field strength, so more field buys either "
         "resolution or time. 3 T is the clinical standard because that gain is real while the "
         "artefacts — susceptibility at air-tissue boundaries, specific absorption rate — are "
         "still manageable.",
         "Tumour volumetry in NF2, muscle fat-fraction in Duchenne, structural brain imaging.",
         "Sub-millimetre, given time. Volumetry reproduces to a few percent WITH a frozen "
         "protocol; changing sequence between visits destroys the comparison you were building.",
         (2_000_000, 3_000_000), 300_000, 1_500_000, 3.0,
         ["Radiographer 2.0", "MR physicist 0.5", "Radiologist 0.5"], None),

    inst("mri7t", "7 T MRI", "clinical imaging",
         "Roughly twice the signal of 3 T, and the usual choice is to spend it on resolution. "
         "The physics pushes back: the radiofrequency wavelength in tissue approaches head "
         "dimensions, so the excitation field goes non-uniform and needs parallel transmit, and "
         "specific absorption rate scales with the square of field strength, which limits the "
         "sequences you are allowed to run.",
         "Small internal-auditory-canal lesions, cortical microstructure.",
         "For a hearing endpoint it is the wrong instrument no matter its resolution — see the "
         "audiometry entry. Resolution was never the missing thing.",
         (8_000_000, 12_000_000), 900_000, 3_000_000, 4.0,
         ["Radiographer 2.0", "MR physicist 1.5", "Radiologist 0.5"],
         "Almost always yes. A 3 T with a dedicated protocol answers most questions a programme "
         "actually has, for a fifth of the capital and a tenth of the siting."),

    inst("audio", "Audiometric booth with ABR and otoacoustic emissions", "clinical function",
         "The booth is the instrument. A hearing threshold cannot be measured below the ambient "
         "noise floor, so the room is built to hold under about 20 dBA — quieter than a library. "
         "The auditory brainstem response then reads the evoked far-field potential, giving a "
         "threshold without the patient cooperating, and otoacoustic emissions test the cochlear "
         "amplifier directly, by listening for the sound a working ear itself produces.",
         "Pure-tone threshold, word recognition, brainstem conduction — the endpoint an NF2 "
         "patient names first, as opposed to a tumour diameter.",
         "5 dB steps by convention. Test-retest variability is the real floor, and it sets how "
         "large an effect a trial can possibly detect.",
         (60_000, 130_000), 15_000, 40_000, 1.5,
         ["Audiologist 1.0", "Technologist 0.5"],
         "It is already the cheapest instrument in this file by two orders of magnitude, and it "
         "is the one that measures what the patient came in for."),

    inst("cryoem", "Cryo-electron microscope, 200-300 kV", "structural",
         "Electrons scatter off matter some ten thousand times more strongly than X-rays, so one "
         "unstained particle in vitreous ice gives usable contrast before radiation damage "
         "destroys it. High accelerating voltage cuts the inelastic fraction and gets the beam "
         "through thicker ice. No crystal is required — which is the whole point for a membrane "
         "protein that refuses to crystallise.",
         "The structure of a mutant channel or transporter, and how a candidate corrector binds.",
         "2-4 angstroms routinely for a well-behaved particle above about 100 kDa. Projects die "
         "at sample preparation, not at the microscope.",
         (2_500_000, 7_000_000), 700_000, 2_000_000, 3.5,
         ["Structural biologist 1.5", "Microscopist 1.0", "Processing and compute 1.0"],
         "National facilities sell microscope time by the day. Buying one to answer a single "
         "structural question is close to never correct."),
]

BY_ID = {i["id"]: i for i in INSTRUMENTS}


# --- duty cycle: how many answers a year, how long the instrument lasts ---------------
# WHY THIS IS SEPARATE FROM THE PRICE. Capital is what an instrument costs to own. It is not
# what an answer costs, and the two rank the instruments differently — which is the finding.
# An instrument amortises over its life and its throughput, so a cheap machine that runs one
# sample a week can cost more per answer than an expensive one that runs a hundred a day.
#
# Throughput is a REALISTIC academic duty cycle, not a datasheet maximum: instruments queue,
# break, wait for staff and sit idle between grants. Manufacturers quote the ceiling; this is
# nearer the floor, and where the two differ the honest number is the lower one. Lifetime is
# years to obsolescence or to a service contract nobody will renew — for sequencing that is
# short and technological, for a shielded room it is long and structural.
#
# Consumable is per unit of the stated unit — a flow cell, a plate, a scan, a batch. The
# bioreactor entry is not a typo: single-use bags, media and resin at that scale genuinely
# dominate everything else in this file, and they are the arithmetic behind the AAV ceiling.
DUTY = {
    #             per year   unit             life   consumable per unit
    "nanopore":   (1_500,    "sample",         5,      400),
    "illumina":   (3_000,    "sample",         6,      250),
    "optical_map":(  800,    "sample",         7,      500),
    "ddpcr":      (8_000,    "reaction",       8,       25),
    "patch":      (6_000,    "cell assay",     7,       60),
    "mea":        (2_000,    "plate",          8,       80),
    "lcms":       (12_000,   "sample",         8,       30),
    "confocal":   (3_000,    "experiment",     8,      120),
    "highcontent":(20_000,   "plate",          7,       15),
    "sorter":     (1_500,    "sort",           8,       90),
    "auc":        (  300,    "run",           10,      200),
    "bioreactor": (   24,    "batch",         10,  180_000),
    "cleanroom":  (   40,    "released batch",20,   60_000),
    "mri3t":      (4_000,    "scan",          10,      180),
    "mri7t":      (2_500,    "scan",          10,      250),
    "audio":      (2_000,    "test",          12,        8),
    "cryoem":     (  250,    "dataset",       10,    1_200),
}

for _i in INSTRUMENTS:
    _n, _unit, _life, _cons = DUTY[_i["id"]]
    _cap = (_i["capexUSD"][0] + _i["capexUSD"][1]) / 2
    # Amortised capital + service and consumables, per answer. The mid-point of the capital
    # band is used here and ONLY here: a per-answer figure carried as a band of a band stops
    # being readable, so the band stays on the capital row where it belongs.
    _i["throughputPerYear"] = _n
    _i["unit"] = _unit
    _i["lifetimeYears"] = _life
    _i["consumablePerUnitUSD"] = _cons
    _i["costPerAnswerUSD"] = round(_cap / (_life * _n) + _i["opexUSDyr"] / _n + _cons)



# --- diagnosis: what the standard test misses, and the instrument that would not ------
def dx(disease, standard, misses, sharper, instruments, physics, per_test, changes):
    return dict(catalogueName=disease, standard=standard, misses=misses, sharper=sharper,
                instruments=instruments, physics=physics, perTestUSD=list(per_test),
                changesManagement=changes)


DIAGNOSTICS = [
    dx("Duchenne muscular dystrophy",
       "MLPA or array for exon deletions and duplications, then panel sequencing.",
       "Roughly 7% of patients: deep-intronic variants that create a pseudo-exon, and inversions "
       "with both breakpoints inside the gene. Both are invisible to a method that counts exons.",
       "Long-read genome plus optical mapping, and muscle RNA sequencing to prove the "
       "pseudo-exon is actually spliced in.",
       ["nanopore", "optical_map", "illumina"],
       "The gene is 2.2 Mb — the largest in the genome. A method whose reads are 150 bp long is "
       "reconstructing a book from shredded lines, and a balanced inversion leaves the exon "
       "count unchanged, so a copy-number method reports normal.",
       (1_800, 4_000),
       "It decides which exon-skipping oligonucleotide, if any, the patient is eligible for — "
       "and a proven pseudo-exon is one of the few targets an n-of-1 antisense can be built to."),

    dx("Cystic fibrosis",
       "Sweat chloride, then a variant panel of the common alleles.",
       "Rare and compound-heterozygous genotypes with no published modulator response. The panel "
       "answers whether you have CF; it does not answer whether the drug will work on YOU.",
       "Patient-derived intestinal organoid swelling — theratyping — read as a live response to "
       "the actual compound.",
       ["confocal", "illumina"],
       "Forskolin raises cyclic AMP, CFTR opens, chloride and then water follow osmotically and "
       "the organoid lumen swells. The measurement is a volume change, so it needs live optical "
       "sectioning over an hour — a fixed endpoint destroys exactly the thing being measured.",
       (2_500, 6_000),
       "It converts an unlicensable rare genotype into evidence a payer can act on for one "
       "person. This is the mechanism by which a single patient reaches a drug already approved."),

    dx("Full NF2-related schwannomatosis",
       "Contrast MRI for tumour burden, plus germline NF2 sequencing.",
       "Mosaicism, where the variant is absent from blood and present in tumour, and — more "
       "importantly — hearing. Tumour volume and hearing decouple: a stable tumour can sit "
       "alongside progressive deafness.",
       "Tumour-tissue deep sequencing for mosaicism, and serial audiometry with word recognition "
       "as the tracked variable from the first visit.",
       ["illumina", "ddpcr", "audio", "mri3t"],
       "A mosaic variant may sit at a few percent allele fraction in blood, under the noise of "
       "standard sequencing; droplet partitioning gives an absolute count instead of a ratio. "
       "And hearing is a cochlear-nerve function, not a volume — no imaging resolution measures "
       "it, because it is not a geometric quantity.",
       (1_200, 3_500),
       "It changes the endpoint. The audiometric booth costs about 4% of the 3 T scanner and "
       "measures the thing the patient actually loses."),

    dx("Proximal spinal muscular atrophy",
       "SMN1 deletion test with SMN2 copy number.",
       "SMN2 copy number is a coarse predictor, and the modifying c.859G>C variant inside SMN2 "
       "is not counted by a copy-number assay at all.",
       "Droplet digital PCR for exact SMN2 copies plus sequencing of the modifier, and blood "
       "neurofilament as a treatment-response marker.",
       ["ddpcr", "illumina", "lcms"],
       "SMN1 and SMN2 differ by a handful of bases, so any relative method is measuring a ratio "
       "of near-identical templates. Poisson partitioning counts molecules instead of comparing "
       "amplification curves, which is the only way 3 copies and 4 copies separate cleanly.",
       (800, 2_000),
       "Copy number drives the treatment decision in pre-symptomatic newborns, where the "
       "difference between acting now and waiting is measured in motor neurons that do not "
       "come back."),

    dx("Dravet syndrome",
       "Epilepsy gene panel; a pathogenic SCN1A variant confirms the diagnosis.",
       "Whether a missense variant is loss- or gain-of-function. The panel reports pathogenic "
       "and stops, and the two directions want opposite drugs.",
       "Functional electrophysiology of the specific variant, and network phenotyping in "
       "patient-derived neurons.",
       ["patch", "mea", "illumina"],
       "Nav1.1 sits mostly in inhibitory interneurons. Losing it removes the brake, so a sodium "
       "channel blocker — the reflex antiepileptic — makes a loss-of-function patient worse. "
       "Only a gigaohm-seal current measurement distinguishes the two, and the leak current in a "
       "poor seal is larger than the signal being argued about.",
       (4_000, 12_000),
       "It is the difference between a drug that helps and a drug that increases seizure "
       "frequency, from the same reported variant."),

    dx("Rett syndrome",
       "MECP2 sequencing plus deletion or duplication analysis.",
       "X-inactivation skew, which explains much of why two girls with the same variant have "
       "very different courses. It is not sequence, so sequencing does not see it.",
       "Long-read sequencing with native methylation calling on the same reads.",
       ["nanopore"],
       "Nanopore reads 5-methylcytosine from the current deviation itself, so methylation and "
       "haplotype come off one molecule and the skew can be phased to an allele. Bisulfite "
       "conversion loses the phase and destroys much of the DNA to get its signal.",
       (900, 2_200),
       "It gives a prognostic axis to a diagnosis that currently has almost none, and it is the "
       "measurement any attempt to reactivate the silent wild-type X would need as its readout."),

    dx("CDKL5-deficiency disorder",
       "Epilepsy panel sequencing of CDKL5.",
       "How much residual kinase activity a given missense variant retains. Nothing in a "
       "sequence report is a rate.",
       "Kinase activity assay on the variant protein, with network phenotyping alongside.",
       ["mea", "highcontent"],
       "The gene encodes an enzyme, and an enzyme has a turnover number. Two variants reported "
       "identically as pathogenic missense can differ tenfold in residual activity, and a "
       "protein-replacement or stabiliser strategy only makes sense above some floor.",
       (5_000, 15_000),
       "It stratifies who could plausibly respond to a stabiliser versus who needs the protein "
       "supplied — two different programmes that are currently one undivided cohort."),

    dx("Zellweger syndrome",
       "Plasma very-long-chain fatty acids, then PEX gene panel.",
       "The mild end. A patient with substantial residual peroxisome assembly can have VLCFA "
       "close enough to normal that the screen never fires.",
       "Quantitative plasmalogen and bile-acid intermediate panel by LC-MS/MS, with fibroblast "
       "peroxisome import imaging.",
       ["lcms", "confocal"],
       "Triple-quadrupole selection of both a precursor and a fragment mass gives the "
       "selectivity to quantify a low-abundance lipid inside plasma; the isotope-labelled "
       "internal standard is what makes the number absolute rather than comparative.",
       (600, 1_800),
       "The mild genotypes are the only ones where a variant-specific intervention has time to "
       "act, and they are precisely the ones the current screen under-detects."),

    dx("Fibrodysplasia ossificans progressiva",
       "Clinical recognition — malformed great toes plus flare-ups — then ACVR1 sequencing.",
       "Almost nothing genetically; the recurrent R206H variant is nearly universal. What is "
       "missed is the flare itself, which is routinely biopsied as a soft-tissue tumour, and the "
       "biopsy triggers new bone.",
       "Recognition first; then imaging that does not require an incision, for lesion activity.",
       ["mri3t"],
       "The diagnosis is visible on the foot at birth, years before the first flare. This is the "
       "one entry in the file where the correct instrument is a trained clinician, and the harm "
       "comes from reaching for a scalpel.",
       (400, 1_200),
       "Avoiding the biopsy is the intervention. Trauma is the trigger, so the diagnostic "
       "procedure itself is the mechanism of injury."),

    dx("Alkaptonuria",
       "Urine that darkens on standing; homogentisic acid confirmation.",
       "Decades. The pigment accumulates from birth and the diagnosis is typically made in the "
       "fourth or fifth decade, after the cartilage damage is done.",
       "Quantitative plasma and urine homogentisic acid by LC-MS/MS, as a treatment-response "
       "measure rather than a yes-or-no.",
       ["lcms"],
       "Nitisinone lowers homogentisic acid by inhibiting the enzyme upstream. The effect is a "
       "concentration, so the endpoint has to be a concentration — and it is measurable years "
       "before any clinical change appears.",
       (300, 900),
       "It is the clean case of a biomarker that acts long before the outcome. Waiting for the "
       "clinical endpoint here means waiting for irreversible damage to appear on schedule."),

    dx("Sickle cell anemia",
       "Haemoglobin electrophoresis or high-performance liquid chromatography.",
       "Almost nothing diagnostically — this disease is easy to diagnose and hard to treat. What "
       "goes unmeasured is fetal haemoglobin distribution ACROSS cells.",
       "Single-cell fetal haemoglobin measurement by flow cytometry, and haplotype modifiers.",
       ["sorter", "illumina", "ddpcr"],
       "Total fetal haemoglobin is an average, and averages lie here: 20% spread evenly across "
       "every red cell protects, while the same 20% concentrated in a fifth of the cells leaves "
       "four fifths of them sickling normally. Only a per-cell measurement separates those.",
       (500, 2_500),
       "It is the right endpoint for every fetal-haemoglobin-induction therapy, including the "
       "approved editing ones, and the cheap small molecules that have never been tested this "
       "way."),

    dx("Systemic lupus erythematosus",
       "Clinical criteria plus autoantibody serology.",
       "Which disease the patient has. Lupus is a label over several biologies, and the "
       "serology does not separate them.",
       "Interferon signature by targeted expression panel, plus immune cell subsets by "
       "high-parameter flow cytometry.",
       ["illumina", "sorter"],
       "There is no physical barrier here at all — the assay is a modest gene panel, and the "
       "instruments are ones that most hospitals already own. The barrier is that it is not "
       "standard, which makes this the cheapest unrealised stratification in the file.",
       (200, 700),
       "Anifrolumab targets interferon signalling. Enrolling a trial without stratifying by the "
       "interferon signature dilutes the responders with people whose disease runs on something "
       "else — the failure mode is a negative trial of an effective drug."),
]


# --- approach plans: stages, gates, instruments, efficacy as it actually stands -------
def plan(id, disease, approach, goal, physics, stages, instruments, efficacy, evidence,
         horizon, note):
    return dict(id=id, catalogueName=disease, approach=approach, goal=goal, physics=physics,
                stages=stages, instruments=instruments, efficacy=efficacy,
                efficacyEvidence=evidence, horizonYears=horizon, note=note)


def st(name, does, needs, gate):
    return dict(name=name, does=does, needs=needs, gate=gate)


PLANS = [
    plan("nf2_local", "Full NF2-related schwannomatosis",
         "Local delivery to the internal auditory canal",
         "Put the agent where the tumour is, and measure hearing rather than diameter.",
         "The vestibular schwannoma sits in a bony canal a few millimetres across, bounded and "
         "reachable. Systemic dosing spreads the agent through 70 kg of patient to treat perhaps "
         "a gram of tissue — the dilution is geometric, and every unit that misses is pure "
         "toxicity. Local administration inverts that ratio by three or four orders of magnitude.",
         [st("Endpoint first", "Freeze word recognition and pure-tone threshold as the primary "
                               "outcome before any dosing, with test-retest variance measured on "
                               "the actual cohort.",
             ["audio"], "Retest variance small enough that a clinically meaningful change is "
                        "detectable in the planned sample size. If it is not, no dose will fix it."),
          st("Vector and route", "Choose a serotype for the target cell and a route — round "
                                 "window, intracanalicular — with distribution measured, not "
                                 "assumed.", ["ddpcr", "auc"],
             "Vector genomes per diploid genome in target tissue, at an acceptable full-to-empty "
             "ratio. Empty capsids delivered next to a nerve are immunogen at close range."),
          st("Volume alongside function", "Serial fixed-protocol MRI, read as a secondary "
                                          "measure and never as the primary.", ["mri3t"],
             "Protocol frozen across visits. A sequence change between scans invalidates the "
             "series that was the entire purpose."),
          st("Dose in the smallest defensible cohort", "Bilateral disease permits a "
             "within-patient control: one side dosed, the other observed.", ["audio", "ddpcr"],
             "Ethics approval for asymmetric dosing, which is the hard part and not a "
             "technical one.")],
         ["audio", "mri3t", "ddpcr", "auc"],
         "unknown",
         "No completed trial has used hearing preservation as a primary endpoint in this "
         "disease. Bevacizumab produced hearing improvement in a minority in open-label series, "
         "which is the closest precedent and is not controlled. The local-delivery step itself "
         "is unproven here, though intracochlear administration is established in other ear "
         "programmes.",
         "5-8",
         "Cheapest plan in the file, and the one whose critical instrument is the booth."),

    plan("cf_theratype", "Cystic fibrosis", "Theratyping in patient-derived organoids",
         "Give one person evidence for a drug that already exists and was never licensed for "
         "their genotype.",
         "The organoid is the patient's own epithelium with the patient's own two alleles. "
         "Forskolin raises cyclic AMP, functional CFTR opens, chloride moves and water follows "
         "osmotically — so the swelling IS the chloride conductance, measured directly rather "
         "than inferred from a population.",
         [st("Biopsy and derive", "Rectal suction biopsy, organoid line established and banked.",
             ["confocal"], "Line grows and passages. This step fails often enough to plan for."),
          st("Response curve", "Full concentration-response to each approved modulator "
                               "combination, against known-responder and known-non-responder "
                               "controls on the same plate.", ["confocal", "highcontent"],
             "Response separated from the non-responder control by more than assay variance. "
             "Same-plate controls are what make it a measurement rather than an anecdote."),
          st("Reimbursement dossier", "The curve, the controls and the analysis assembled for a "
                                      "payer, since this is a funding decision and not a "
                                      "regulatory one.", [],
             "Payer accepts the assay as evidence — the actual bottleneck, and it is "
             "jurisdictional.")],
         ["confocal", "illumina", "highcontent"],
         "demonstrated",
         "Organoid swelling response has predicted individual clinical response, and in the "
         "Netherlands it has been used to grant access for rare genotypes outside the label. "
         "This is the strongest-evidenced entry in the file, and it needs no new molecule at all.",
         "1-2",
         "The template generalises: any disease with an approved drug, a rare genotype and a "
         "measurable cellular readout can copy it."),

    plan("dravet_functional", "Dravet syndrome", "Function before prescription",
         "Establish loss- or gain-of-function for the specific variant before choosing a drug.",
         "Nav1.1 is concentrated in inhibitory interneurons. Removing it disinhibits the network, "
         "so a sodium-channel blocker deepens the very deficit causing the seizures. The sign of "
         "the functional change decides the direction of treatment, and it is not in the "
         "sequence.",
         [st("Express the variant", "The patient's exact variant in a heterologous cell line "
                                    "alongside the wild-type channel.", ["patch"],
             "Seal resistance above one gigaohm on enough cells. Below that, the leak is larger "
             "than the current under discussion."),
          st("Confirm in the patient's own cells", "iPSC-derived neurons, network firing on the "
             "array.", ["mea"], "Network phenotype separates from isogenic control."),
          st("Report a direction", "The clinical report says loss or gain, not merely "
                                   "pathogenic.", [], "Direction stated with its uncertainty.")],
         ["patch", "mea", "illumina"],
         "established mechanism, unmeasured programme benefit",
         "That sodium-channel blockers worsen Dravet is well established clinically. That "
         "routine functional testing improves outcomes at the population level has not been "
         "trialled — the practice is right on mechanism and unquantified as a policy.",
         "2-3",
         "A manual patch rig at $80-150k does this for one family. The automated instrument is "
         "for the service, not for the answer."),

    plan("dmd_reframe", "Duchenne muscular dystrophy", "CRISPR reframing rather than exon skipping",
         "Restore the reading frame permanently in muscle instead of re-dosing an "
         "oligonucleotide for life.",
         "Exon skipping works at the message, so it is consumed and must be given again forever, "
         "and it never reaches enough muscle. Editing works at the genome, so one successful "
         "edit persists in that nucleus. The obstacle is arithmetic: skeletal muscle is roughly "
         "40% of body mass, and there is no vector dose that reaches it all.",
         [st("Genotype completely", "Long reads and optical mapping, so the breakpoints are "
                                    "known rather than inferred.", ["nanopore", "optical_map"],
             "Both breakpoints resolved to base pair. A guide designed against an inferred "
             "breakpoint edits nothing."),
          st("Guide design and off-target", "Candidate guides screened for on-target efficiency "
             "and unbiased off-target.", ["ddpcr", "illumina", "highcontent"],
             "On-target editing measurable and off-target below detection, where detection means "
             "droplet-level sensitivity and not a gel."),
          st("Vector at dose", "Manufacture at the vector genome count a systemic dose "
                               "requires.", ["bioreactor", "auc", "ddpcr"],
             "This is the wall. 2e15 genomes for one 20 kg child, at an acceptable full-to-empty "
             "ratio, and the immune response to that capsid load is dose-limiting and "
             "occasionally fatal."),
          st("Read out the protein, not the edit", "Muscle biopsy immunofluorescence for "
             "dystrophin, and function.", ["confocal", "mri3t"],
             "Dystrophin-positive fibres above the threshold where function plausibly follows — "
             "a threshold that is itself contested.")],
         ["nanopore", "optical_map", "ddpcr", "bioreactor", "auc", "confocal", "mri3t"],
         "unproven in humans",
         "Reframing restores dystrophin in mouse and dog models with durable expression. In "
         "humans, systemic AAV in this disease has caused fatal immune and hepatic events, and "
         "no editing programme has yet shown functional benefit. The manufacturing dose is the "
         "binding constraint, not the editing chemistry.",
         "8-12",
         "The most expensive plan here by an order of magnitude, and the one whose central "
         "problem is a bioreactor rather than a nuclease."),

    plan("rett_xreact", "Rett syndrome", "Reactivating the silent wild-type X",
         "Every cell already carries a good copy. Turn it back on instead of delivering a new one.",
         "Rett girls are mosaic: about half their cells silenced the healthy allele by X "
         "inactivation. That allele is intact and present — the fix is epigenetic, not genetic, "
         "which is why no vector has to carry a gene anywhere.",
         [st("Measure the skew", "Phased methylation on native long reads, per tissue.",
             ["nanopore"], "Skew quantified and phased to an allele. Without phase you cannot "
                           "tell reactivation from noise."),
          st("Screen for reactivation", "Compound and guide screens on a reporter line that "
             "lights up when the silent allele speaks.", ["highcontent", "sorter"],
             "A reporter with a signal window wide enough to screen against."),
          st("Check specificity", "The X carries about 800 genes. Reactivating them all is not "
             "a therapy.", ["illumina", "ddpcr"],
             "Selectivity for the locus over the chromosome — the step that has repeatedly "
             "failed and the reason this remains preclinical."),
          st("Function in neurons", "Patient-derived neurons, network measures.", ["mea"],
             "Phenotype moves toward isogenic control.")],
         ["nanopore", "highcontent", "sorter", "mea", "illumina"],
         "preclinical only",
         "Reactivation of the silent X has been demonstrated in mouse models and in cells, with "
         "partial phenotypic rescue. Selectivity remains the unsolved problem and nothing has "
         "entered clinical trial. Meanwhile MECP2 dosage is bidirectionally toxic — duplication "
         "is its own disease — so over-reactivation is a real hazard, not a theoretical one.",
         "10-15",
         "Elegant, genuinely underused, and honestly far away. The dosage window is the thing "
         "that makes it hard."),

    plan("scd_hbf", "Sickle cell anemia", "Fetal haemoglobin induction by small molecule",
         "Reach the many, not the few, by using a pill rather than a transplant.",
         "Fetal haemoglobin interrupts the polymer that deforms the cell. Editing achieves that "
         "and requires myeloablative conditioning, apheresis and a transplant unit — which "
         "excludes most of the world's patients on infrastructure alone, not on biology.",
         [st("Measure per cell, not on average", "Single-cell fetal haemoglobin by flow "
                                                 "cytometry as the primary pharmacodynamic "
                                                 "readout.", ["sorter"],
             "F-cell distribution measurable and reproducible. A total percentage hides the "
             "distribution that decides whether cells sickle."),
          st("Screen the existing shelf", "Compounds already approved for other indications, "
             "profiled in erythroid culture.", ["highcontent", "sorter"],
             "Induction beyond hydroxyurea in the same assay, on the same plates."),
          st("Confirm the mechanism", "Whether induction is transcriptional or a survival "
                                      "artefact of selecting F-cells.", ["ddpcr", "illumina"],
             "Mechanism distinguished. Selection dressed as induction is a common and expensive "
             "way to be wrong."),
          st("Trial where the patients are", "Design for settings without transplant "
                                             "infrastructure.", ["sorter"],
             "Endpoint measurable on a benchtop cytometer, which most sites can actually have.")],
         ["sorter", "highcontent", "ddpcr", "illumina"],
         "partially demonstrated",
         "Hydroxyurea induces fetal haemoglobin and reduces crises — proven, cheap and still "
         "under-prescribed. Voxelotor and the approved editing therapies work by other routes at "
         "very different costs. That better small-molecule inducers exist and are untested is a "
         "judgement; that the per-cell distribution matters more than the average is established.",
         "3-6",
         "The only plan in the file whose main claim is that a cheaper instrument reaches more "
         "people than a better one."),

    plan("lupus_stratify", "Systemic lupus erythematosus",
         "Interferon signature stratification at enrolment",
         "Stop diluting responders with people whose disease runs on something else.",
         "There is no physics obstacle at all. The assay is a modest expression panel on "
         "instruments most hospitals already own. The barrier is entirely convention.",
         [st("Panel and threshold", "A targeted interferon-stimulated gene panel with a "
                                    "pre-registered threshold.", ["illumina"],
             "Threshold fixed BEFORE the trial. Chosen afterwards, it is a subgroup analysis "
             "and worth much less."),
          st("Immune subsets", "High-parameter flow alongside, for the mechanism.", ["sorter"],
             "Panel validated across sites."),
          st("Stratified randomisation", "Signature-high and signature-low randomised "
                                         "separately.", [],
             "Both strata powered, so a negative result in one is informative rather than empty.")],
         ["illumina", "sorter"],
         "partially demonstrated",
         "Anifrolumab, which blocks type I interferon signalling, is approved and shows a larger "
         "effect in signature-high patients. Stratifying at enrolment rather than analysing "
         "afterwards has still not become routine. Cost per patient is a few hundred dollars "
         "against a trial that costs tens of thousands per patient.",
         "1-3",
         "The cheapest unrealised change in the file, and the one with the least physics in it."),
]


def money(lo, hi):
    return dict(lo=lo, hi=hi)


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)

    # roll the per-plan instrument list up into capital, operating and people
    for p in PLANS:
        ids = p["instruments"]
        missing = [i for i in ids if i not in BY_ID]
        if missing:
            raise SystemExit("plan %s references unknown instruments: %s" % (p["id"], missing))
        chosen = [BY_ID[i] for i in ids]
        p["capexUSD"] = money(sum(c["capexUSD"][0] for c in chosen),
                              sum(c["capexUSD"][1] for c in chosen))
        p["opexUSDyr"] = sum(c["opexUSDyr"] for c in chosen)
        p["sitingUSD"] = sum(c["sitingUSD"] for c in chosen)
        p["fte"] = round(sum(c["fte"] for c in chosen), 1)
        p["roles"] = sorted({r for c in chosen for r in c["roles"]})

    for d in DIAGNOSTICS:
        missing = [i for i in d["instruments"] if i not in BY_ID]
        if missing:
            raise SystemExit("diagnostic %s references unknown: %s" % (d["catalogueName"], missing))

    klasses = Counter(i["klass"] for i in INSTRUMENTS)
    eff = Counter(p["efficacy"] for p in PLANS)

    payload = {
        "generated": "tools/capability_seed.py",
        "premise": (
            "An approach is not an idea; it is a room, an instrument, a physical limit and a "
            "payroll. Each instrument below carries the reason the measurement cannot be made "
            "another way, and — where one exists — the cheaper route that would do."
        ),
        "provenance": (
            "The physics is textbook and checkable. The cost bands are engineering estimates in "
            "2025-2026 US dollars: order-of-magnitude list prices, right to about a factor of "
            "two and not to a decimal, since list price is not transaction price. Operating cost "
            "is service contract plus consumables — service alone runs 8-12% of capital a year, "
            "which is why a donated instrument is not a free one. Siting is carried separately "
            "because for the largest instruments it exceeds the instrument. Staff is FTE, not "
            "headcount. Nothing here is a procurement quote and nothing here is clinical "
            "guidance."
        ),
        "instruments": INSTRUMENTS,
        "diagnostics": DIAGNOSTICS,
        "plans": PLANS,
        "summary": {
            "instruments": len(INSTRUMENTS),
            "byClass": dict(klasses),
            "withCheaperRoute": sum(1 for i in INSTRUMENTS if i["cheaperRoute"]),
            "diagnostics": len(DIAGNOSTICS),
            "plans": len(PLANS),
            "planStages": sum(len(p["stages"]) for p in PLANS),
            "byEfficacy": dict(eff),
            "capexRangeUSD": money(min(i["capexUSD"][0] for i in INSTRUMENTS),
                                   max(i["capexUSD"][1] for i in INSTRUMENTS)),
            "cheapestAnswerUSD": min(i["costPerAnswerUSD"] for i in INSTRUMENTS),
            "dearestAnswerUSD": max(i["costPerAnswerUSD"] for i in INSTRUMENTS),
            "cheapestPlanUSD": min(p["capexUSD"]["lo"] for p in PLANS),
            "dearestPlanUSD": max(p["capexUSD"]["hi"] for p in PLANS),
        },
    }

    path = DEST / "capability.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    s = payload["summary"]
    print("wrote %s" % path.relative_to(ROOT))
    print("  %d instruments (%d state a cheaper route) · %d diagnostics · %d plans, %d stages"
          % (s["instruments"], s["withCheaperRoute"], s["diagnostics"], s["plans"],
             s["planStages"]))
    print("  instrument capital spans $%s to $%s"
          % (format(s["capexRangeUSD"]["lo"], ","), format(s["capexRangeUSD"]["hi"], ",")))
    print("  plan capital spans $%s to $%s"
          % (format(s["cheapestPlanUSD"], ","), format(s["dearestPlanUSD"], ",")))
    print("  efficacy as it actually stands: %s" % s["byEfficacy"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
