from collections import Counter
from project7_agent.dataset import generate_cases


def test_balanced_40_case_benchmark():
    cases=generate_cases(); assert len(cases)==40; assert set(Counter(c.category for c in cases).values())=={5}; assert Counter(c.split for c in cases)=={"development":8,"test":32}
