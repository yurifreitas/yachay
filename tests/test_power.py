"""Stage 2 — Power. Tests for the stage that says what a sample could not have found.

The stage was extracted from arithmetic that was living inline in `tools/dossier.py`
(docs/audit.md A15). These tests exist because the extraction has to be provably identical
to what it replaced, and because a power calculation is exactly the kind of code that is
plausible when wrong: every formula here returns a positive number for any input, so
"it ran" tells you nothing.
"""

from __future__ import annotations

import math

import pytest

import sieve as sv


class TestMinimumDetectableEffect:
    def test_matches_the_closed_form_by_hand(self):
        """The one number a reader should be able to check on paper."""
        # (1.95996 + 0.84162) * sqrt(4/26) = 2.80158 * 0.392232 = 1.09884
        assert sv.min_detectable_effect(26).at() == 1.099

    def test_falls_as_the_square_root_of_n(self):
        """Quadrupling the sample halves the detectable effect. Not linear — this is the
        fact that makes small trials so much worse than people expect."""
        small = sv.min_detectable_effect(100).floor
        big = sv.min_detectable_effect(400).floor
        assert big == pytest.approx(small / 2, rel=1e-3)

    def test_the_rare_disease_case_cannot_see_a_large_effect(self):
        """26 patients is the median interventional trial across this project's portfolio."""
        d = sv.min_detectable_effect(26)
        assert not d.can_detect_large
        assert d.verdict == "cannot find even a large effect"

    def test_a_registry_scale_study_can(self):
        d = sv.min_detectable_effect(2000)
        assert d.can_detect_large
        assert d.floor < 0.2

    def test_refuses_a_sample_too_small_to_mean_anything(self):
        """Returning a number here would be worse than raising: it would be quoted."""
        with pytest.raises(sv.PowerError):
            sv.min_detectable_effect(2)

    def test_carries_its_assumptions_with_it(self):
        """A floor quoted without its model is the defect this library exists to catch."""
        assert "flatters" in sv.min_detectable_effect(100).assumptions


class TestRequiredN:
    def test_is_the_inverse_of_the_floor(self):
        """Round-trip: the n required for an effect must be able to detect that effect."""
        for effect in (0.2, 0.5, 0.8, 1.0):
            n = sv.required_n(effect)
            assert sv.min_detectable_effect(n).floor <= effect + 1e-9

    def test_rounds_up_and_the_direction_is_not_a_taste(self):
        """One patient below the requirement is under-powered by construction."""
        effect = 0.8
        n = sv.required_n(effect)
        assert sv.min_detectable_effect(n - 1).floor > effect

    def test_a_smaller_effect_needs_a_bigger_study(self):
        assert sv.required_n(0.2) > sv.required_n(0.5) > sv.required_n(0.8)

    def test_refuses_a_null_effect(self):
        with pytest.raises(sv.PowerError):
            sv.required_n(0)


class TestProportions:
    def test_refuses_the_normal_approximation_where_it_is_anti_conservative(self):
        """Below five expected events the approximation understates the difference — the
        worst direction for a bound whose job is to say "you could not have seen this"."""
        with pytest.raises(sv.PowerError) as e:
            sv.min_detectable_proportion_difference(6, 0.5)
        assert "anti-conservative" in str(e.value)

    def test_works_where_it_is_honest(self):
        d = sv.min_detectable_proportion_difference(100, 0.5)
        assert 0 < d < 1

    def test_a_rarer_baseline_is_easier_to_move_in_absolute_terms(self):
        """Variance is maximal at 0.5, so the detectable absolute difference is largest
        there. A reader who expects the opposite is thinking in relative terms."""
        at_half = sv.min_detectable_proportion_difference(200, 0.5)
        at_tenth = sv.min_detectable_proportion_difference(200, 0.1)
        assert at_tenth < at_half


class TestPerEntity:
    """The part that makes this a stage rather than a formula: a screen has one sample
    size per entity, which is the premise of the whole library."""

    def test_counts_the_entities_that_had_no_chance(self):
        counts = [10, 20, 30, 40, 5000]
        out = sv.underpowered(counts, 0.8)
        assert out["requiredN"] == sv.required_n(0.8)
        assert out["underpowered"] == 4
        assert out["share"] == pytest.approx(0.8)

    def test_excludes_rather_than_imputes_the_unusable(self):
        """An entity with n=1 is not under-powered — it is unassessable, and merging the
        two would let a count of rumours pass as a count of weak studies."""
        out = sv.underpowered([1, 2, 100, 200], 0.5)
        assert out["tooSmallToAssess"] == 2
        assert out["entities"] == 2

    def test_reports_the_median_entity_not_only_the_count(self):
        out = sv.underpowered([10, 26, 40], 0.8)
        assert out["medianCount"] == 26
        assert out["medianFloor"] == sv.min_detectable_effect(26).at()

    def test_an_empty_screen_does_not_divide_by_zero(self):
        out = sv.underpowered([], 0.8)
        assert out["share"] is None and out["entities"] == 0


class TestGuardsOnTheParameters:
    def test_refuses_an_unlisted_alpha_rather_than_interpolating(self):
        """A power calculation quietly done at the wrong alpha is the class of error this
        stage exists to catch, so the stage must not commit it."""
        with pytest.raises(sv.PowerError):
            sv.min_detectable_effect(100, alpha=0.037)

    def test_refuses_an_unlisted_power(self):
        with pytest.raises(sv.PowerError):
            sv.min_detectable_effect(100, power=0.77)

    def test_higher_power_demands_a_bigger_sample(self):
        assert sv.required_n(0.5, power=0.90) > sv.required_n(0.5, power=0.80)

    def test_stricter_alpha_demands_a_bigger_sample(self):
        assert sv.required_n(0.5, alpha=0.01) > sv.required_n(0.5, alpha=0.05)


def test_the_extraction_reproduces_what_it_replaced():
    """`tools/dossier.py` computed this inline before Stage 2 existed. The published
    portfolio numbers must not move because the code moved (docs/audit.md A15)."""
    published = {26: 1.099, 25: 1.121, 30: 1.023, 32: 0.991, 40: 0.886, 47: 0.817,
                 48: 0.809, 50: 0.792}
    for n, floor in published.items():
        assert sv.min_detectable_effect(n).at() == floor, (
            f"n={n} now gives {sv.min_detectable_effect(n).at()}, published {floor}"
        )
