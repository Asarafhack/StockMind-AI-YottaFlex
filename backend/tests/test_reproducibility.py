import pytest
from data_engine.generators.synthetic_generator import SyntheticDataGenerator

def test_fixed_seed_reproducibility():
    seed = 20261022
    gen_1 = SyntheticDataGenerator(seed=seed)
    gen_2 = SyntheticDataGenerator(seed=seed)

    prods_1 = gen_1.generate_products(20)
    prods_2 = gen_2.generate_products(20)

    assert prods_1 == prods_2
    assert [p["product_id"] for p in prods_1] == [p["product_id"] for p in prods_2]

    locs_1 = gen_1.generate_locations(10)
    locs_2 = gen_2.generate_locations(10)
    assert locs_1 == locs_2

    skus_1 = gen_1.generate_skus(50, prods_1)
    skus_2 = gen_2.generate_skus(50, prods_2)
    assert skus_1 == skus_2
    assert [s["selling_price"] for s in skus_1] == [s["selling_price"] for s in skus_2]

def test_different_seeds_produce_different_distributions():
    gen_a = SyntheticDataGenerator(seed=20261022)
    gen_b = SyntheticDataGenerator(seed=99999999)

    skus_a = gen_a.generate_skus(10, gen_a.generate_products(5))
    skus_b = gen_b.generate_skus(10, gen_b.generate_products(5))

    prices_a = [s["selling_price"] for s in skus_a]
    prices_b = [s["selling_price"] for s in skus_b]
    assert prices_a != prices_b
