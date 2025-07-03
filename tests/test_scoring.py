from reputation import wilson

def test_wilson_values():
    # empty denominator guard
    assert wilson(0, 0) == 0.0
    # 10/10 at 95 % CI ≈ 0.722
    assert 0.70 < wilson(10, 10) < 0.75
    # 7/10 comes out ≈ 0.397
    assert 0.35 < wilson(7, 10) < 0.45
