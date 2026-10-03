"""Determinism: same seed -> identical truth hashes."""

from campus_synth.config import get_profile
from campus_synth.generator import generate_all
from campus_synth.utils import hash_frame


def test_determinism_same_seed_same_hashes():
    cfg = get_profile("small", seed=42, defects=0.0)
    t1, _ = generate_all(cfg)
    t2, _ = generate_all(cfg)
    for name in ["buildings", "spaces", "assets", "meters"]:
        assert hash_frame(t1[name]) == hash_frame(t2[name]), name


def test_different_seeds_differ():
    c1 = get_profile("small", seed=42, defects=0.0)
    c2 = get_profile("small", seed=43, defects=0.0)
    t1, _ = generate_all(c1)
    t2, _ = generate_all(c2)
    assert hash_frame(t1["buildings"]) != hash_frame(t2["buildings"])
