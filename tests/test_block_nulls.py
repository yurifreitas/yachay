"""The null must be shaped like an entity, not like a pooled row.

The defect these tests pin down shipped, and it produced both of the anomalies recorded in
`docs/lineage.md` §8. Pooling control observations across entities and drawing rows i.i.d.
builds a null that describes a *synthetic entity assembled from many real ones*: it carries
the within-entity spread but none of the variance BETWEEN entities. Its sd is therefore too
small, and every z divided by it is too large.

On DepMap that was worth a mean z of -4.09 for control genes that are the null by
construction. `blocks=` fixes it by drawing an entity first, then that entity's
observations.
"""

from __future__ import annotations

import numpy as np
import pytest

import sieve as sv


def _pool(rng, n_entities=200, per_entity=60, between_sd=1.0, within_sd=1.0):
    """A control pool with BOTH variance components, and the labels naming them.

    Every entity is inert — its observations are centred on its own offset, and the
    offsets themselves average zero. Nothing here carries an effect. The only question is
    whether the null notices that entities differ from each other.
    """
    offsets = rng.normal(0.0, between_sd, size=n_entities)
    rows = rng.normal(offsets[:, None], within_sd, size=(n_entities, per_entity))
    labels = np.repeat(np.arange(n_entities), per_entity)
    return rows.reshape(-1, 1), labels, offsets


def test_pooled_null_understates_the_spread_of_a_real_entity():
    """The defect itself, stated as a measurement rather than an opinion."""
    rng = np.random.default_rng(0)
    control, labels, _ = _pool(rng)
    stat = sv.top_k_mean(5)
    counts = np.full(50, 30)

    pooled = sv.fit_null(control, stat, observed_counts=counts, reduce="raw",
                         n_draws=1500, seed=0)
    blocked = sv.fit_null(control, stat, observed_counts=counts, reduce="raw",
                          n_draws=1500, seed=0, blocks=labels)

    # Between-entity variance has to land somewhere. With blocks it lands in the null's
    # spread, which is where it belongs.
    assert blocked.sd[0] > pooled.sd[0] * 1.5, (
        f"blocked sd {blocked.sd[0]:.4f} vs pooled {pooled.sd[0]:.4f}: the pooled null "
        "is not understating the spread, so this test is not measuring the defect"
    )


def test_inert_entities_calibrate_near_zero_only_with_blocks():
    """The consequence: controls that do nothing must score like nothing.

    This is the synthetic form of the DepMap -4.09. Entities drawn from the control
    distribution itself are the null by construction; a correct null puts them at z ~ 0
    with sd ~ 1. The pooled null does not.
    """
    rng = np.random.default_rng(1)
    control, labels, offsets = _pool(rng)
    stat = sv.top_k_mean(5)
    n = 30

    # Score each control entity exactly as the screen would score a real one.
    scores = np.array([
        float(stat(rng.normal(offsets[i], 1.0, size=(1, n)))[0])
        for i in range(len(offsets))
    ])
    counts = np.full(len(scores), n)

    pooled = sv.fit_null(control, stat, observed_counts=counts, reduce="raw",
                         n_draws=2000, seed=0)
    blocked = sv.fit_null(control, stat, observed_counts=counts, reduce="raw",
                          n_draws=2000, seed=0, blocks=labels)

    z_pooled = pooled.z(scores, counts)
    z_blocked = blocked.z(scores, counts)

    # The pooled null inflates the spread of z far beyond 1 -- that inflation IS the bug.
    assert z_pooled.std(ddof=1) > 2.0, (
        f"pooled sd(z) = {z_pooled.std(ddof=1):.2f}; expected the defect to inflate it"
    )
    assert 0.6 < z_blocked.std(ddof=1) < 1.8, (
        f"blocked sd(z) = {z_blocked.std(ddof=1):.2f}; a correct null should put inert "
        "entities near unit spread"
    )
    assert abs(z_blocked.mean()) < 0.5, (
        f"blocked mean z = {z_blocked.mean():.3f}; inert entities must centre on zero"
    )


def test_blocks_flatten_the_slope_in_n():
    """The second symptom: the pooled null's mean rises too steeply with n.

    That is what over-corrects high-n entities and made the count correlation move the
    wrong way on DepMap (-0.0252 -> -0.0559, 95% CI [-0.0344, -0.0271]).
    """
    rng = np.random.default_rng(2)
    control, labels, _ = _pool(rng)
    stat = sv.top_k_mean(5)
    counts = np.array([10, 200])

    pooled = sv.fit_null(control, stat, observed_counts=counts, reduce="raw",
                         n_draws=1500, seed=0, grid=[10, 200])
    blocked = sv.fit_null(control, stat, observed_counts=counts, reduce="raw",
                          n_draws=1500, seed=0, grid=[10, 200], blocks=labels)

    rise_pooled = pooled.mean[-1] - pooled.mean[0]
    rise_blocked = blocked.mean[-1] - blocked.mean[0]
    assert rise_blocked < rise_pooled, (
        f"rise with n: pooled {rise_pooled:.4f}, blocked {rise_blocked:.4f} — the blocked "
        "null should not climb faster than the pooled one"
    )


def test_too_few_blocks_raises_rather_than_guessing():
    """Between-block variance cannot be estimated from a handful of blocks."""
    rng = np.random.default_rng(3)
    control, _, _ = _pool(rng, n_entities=5, per_entity=200)
    labels = np.repeat(np.arange(5), 200)
    with pytest.raises(ValueError, match="too few"):
        sv.fit_null(control, sv.top_k_mean(3), observed_counts=np.full(10, 20),
                    reduce="raw", n_draws=200, blocks=labels)


def test_mislabelled_blocks_raise():
    rng = np.random.default_rng(4)
    control, labels, _ = _pool(rng)
    with pytest.raises(ValueError, match="one label per row"):
        sv.fit_null(control, sv.top_k_mean(3), observed_counts=np.full(10, 20),
                    reduce="raw", n_draws=200, blocks=labels[:-1])
