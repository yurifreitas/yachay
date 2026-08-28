"""Stage 7 — target assessment. Tests for a stage whose job is partly to REFUSE.

Most of these assert that the stage declines to admit a strategy, which is unusual and is
the point: a target model that always produces an answer is a target model that produces one
when it should not. The failure mode being guarded against is a missing axis reading as a
negative one — an unmeasured gene coming back as "not pan-essential" and therefore
knockable.
"""

from __future__ import annotations

import pytest

import sieve as sv
from sieve.stages import target as t


def admitted(a) -> set[str]:
    return set(a.admitted)


class TestUnknownIsNotZero:
    """The central contract: `None` means unmeasured and must block, never permit."""

    def test_an_empty_assessment_admits_nothing(self):
        a = sv.assess("NOTHING_KNOWN")
        assert a.admitted == []
        assert len(a.unknown_axes) == len(a.evidence)

    def test_unmeasured_essentiality_blocks_knockdown(self):
        """Knocking down a gene without knowing whether every cell needs it is the
        failure Stage 3 exists to prevent."""
        a = sv.assess("X", most_recurrent=50, consequences={"missense": 10})
        assert "knockdown or knockout" not in admitted(a)
        why = next(s.because for s in a.strategies if s.name == "knockdown or knockout")
        assert "not measured" in why

    def test_unmeasured_spectrum_blocks_allele_specific_editing(self):
        a = sv.assess("X", pan_essential=False)
        assert "allele-specific editing" not in admitted(a)

    def test_a_measured_zero_is_not_the_same_as_unmeasured(self):
        """most_recurrent=1 is a measurement (no recurrence); None is an absence."""
        measured = sv.assess("X", most_recurrent=1, consequences={"missense": 5})
        unmeasured = sv.assess("X", consequences={"missense": 5})
        assert "allele-specific editing" not in admitted(measured)
        assert "allele-specific editing" not in admitted(unmeasured)
        assert "not measured" not in next(
            s.because for s in measured.strategies if s.name == "allele-specific editing")


class TestStrategies:
    def test_a_recurrent_allele_admits_allele_specific_editing(self):
        a = sv.assess("NF1", most_recurrent=107, consequences={"missense": 369})
        assert "allele-specific editing" in admitted(a)

    def test_a_private_spectrum_does_not(self):
        a = sv.assess("RARE1", most_recurrent=2, consequences={"missense": 40})
        assert "allele-specific editing" not in admitted(a)

    def test_pan_essentiality_blocks_knockdown_even_with_everything_else(self):
        """The one hard veto: a gene every cell needs is not a knockdown target, however
        good its allelic spectrum is."""
        a = sv.assess("SNRPD3", most_recurrent=99, consequences={"missense": 100},
                      pan_essential=True, vus_share=0.1, quantified_signs=20)
        assert "knockdown or knockout" not in admitted(a)
        assert any(g.stage == 3 and not g.passed for g in a.gates)

    def test_an_indel_dominated_spectrum_rules_out_base_editing(self):
        a = sv.assess("X", consequences={"deletion": 60, "insertion": 20, "missense": 10})
        assert "base editing" not in admitted(a)

    def test_a_truncating_spectrum_admits_skipping_and_replacement(self):
        a = sv.assess("DMD", consequences={"frameshift": 60, "nonsense": 20, "missense": 20},
                      private_share=0.9)
        assert {"exon skipping", "gene replacement"} <= admitted(a)

    def test_a_missense_spectrum_admits_neither(self):
        a = sv.assess("X", consequences={"missense": 95, "nonsense": 5}, private_share=0.5)
        assert "exon skipping" not in admitted(a)
        assert "gene replacement" not in admitted(a)


class TestGates:
    def test_no_quantified_endpoint_fails_the_power_gate(self):
        a = sv.assess("X", quantified_signs=0)
        assert any(g.stage == 2 and not g.passed for g in a.gates)

    def test_a_high_vus_share_fails_the_prior_gate(self):
        """Above the threshold a new patient's variant is more likely than not to be
        uninterpretable — an eligibility problem before a therapeutic one."""
        a = sv.assess("X", vus_share=0.85)
        gate = next(g for g in a.gates if g.stage == 6)
        assert not gate.passed and "uncertain" in gate.because

    def test_a_low_vus_share_passes_it(self):
        assert next(g for g in sv.assess("X", vus_share=0.1).gates if g.stage == 6).passed

    def test_thresholds_are_arguments_not_constants(self):
        """A reader who disagrees with a gate must be able to move it without editing the
        library — which is the whole reason this is not a composite score."""
        strict = sv.assess("X", most_recurrent=20, recurrent_allele_patients=50)
        loose = sv.assess("X", most_recurrent=20, recurrent_allele_patients=10)
        assert "allele-specific editing" not in admitted(strict)
        assert "allele-specific editing" in admitted(loose)


class TestShortlistIsASetProperty:
    def test_it_refuses_to_claim_diversification_without_a_module_map(self):
        """Reactome is ingested and unread, so this is the live case — and returning a
        shortlist that merely LOOKS diversified would be the failure Stage 7 names."""
        picks = [sv.assess(g, most_recurrent=20, consequences={"missense": 30},
                           pan_essential=False, vus_share=0.1, quantified_signs=3)
                 for g in ("A", "B", "C")]
        out = sv.shortlist(picks)
        assert out["diversified"] is None
        assert "COULD NOT BE CHECKED" in out["says"]

    def test_a_concentrated_shortlist_is_flagged(self):
        picks = [sv.assess(g, most_recurrent=20, consequences={"missense": 30},
                           pan_essential=False, vus_share=0.1, quantified_signs=3)
                 for g in ("A", "B", "C", "D")]
        out = sv.shortlist(picks, modules={g: "RAS-MAPK" for g in "ABCD"}, slots=4)
        assert out["diversified"] is False
        assert "fails together" in out["says"]

    def test_a_spread_shortlist_is_not(self):
        picks = [sv.assess(g, most_recurrent=20, consequences={"missense": 30},
                           pan_essential=False, vus_share=0.1, quantified_signs=3)
                 for g in ("A", "B", "C", "D")]
        mods = {"A": "RAS-MAPK", "B": "Hippo", "C": "mTOR", "D": "cilium"}
        assert sv.shortlist(picks, modules=mods, slots=4)["diversified"] is True

    def test_a_gene_failing_a_gate_does_not_reach_the_shortlist(self):
        good = sv.assess("GOOD", most_recurrent=20, consequences={"missense": 30},
                         pan_essential=False, vus_share=0.1, quantified_signs=3)
        bad = sv.assess("BAD", most_recurrent=20, consequences={"missense": 30},
                        pan_essential=True, vus_share=0.9, quantified_signs=0)
        out = sv.shortlist([good, bad], modules={"GOOD": "m1", "BAD": "m2"})
        assert out["genes"] == ["GOOD"]


def test_every_strategy_explains_itself():
    """A verdict with no reason is not reviewable, and review is the entire point."""
    a = sv.assess("X", most_recurrent=5, consequences={"missense": 3}, vus_share=0.9)
    for s in a.strategies:
        assert s.because and len(s.because) > 20
    for g in a.gates:
        assert g.because
