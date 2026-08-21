import numpy as np

from app.materials import PROTOTYPES, cosine, get_classifier, noisy_signature


def test_metals_are_closer_to_each_other_than_to_leather():
    brass_steel = cosine(PROTOTYPES["brass"], PROTOTYPES["steel"])
    brass_leather = cosine(PROTOTYPES["brass"], PROTOTYPES["leather"])
    assert brass_steel > 0.75
    assert brass_steel > brass_leather + 0.2


def test_classifier_recovers_brass_from_noisy_spectrum():
    rng = np.random.default_rng(0)
    spectrum = noisy_signature("brass", rng, noise=0.03)
    guess = get_classifier().predict(spectrum)
    assert guess.material == "brass"
    assert guess.family == "metal"
    assert guess.confidence > 0.4
