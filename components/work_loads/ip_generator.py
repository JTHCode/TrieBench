import random
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from faker import Faker

## === Config Class === ##

@dataclass
class IPConfig:
    """
    Configuration for IPGenerator
        public_share: float, proportion of public IPs
        private_weights: dict, weights for private IPs {a: x, b: x, c: x}
        seed: int, seed for random number generator
    """
    public_share: float = 0.9  # fraction of public IPs
    private_weights: Optional[Dict[str, float]] = None  # weights for {'a','b','c'}
    seed: Optional[int] = None  # seed for random number generator

    def __post_init__(self):
        if self.private_weights is None:
            self.private_weights = {'a': 0.35, 'b': 0.10, 'c': 0.55}
        else:
            missing = [k for k in ('a','b','c') if k not in self.private_weights]
            if missing:
                raise ValueError(f"private_weights missing keys: {missing}")
            if any(self.private_weights[k] < 0 for k in ('a','b','c')):
                raise ValueError("private_weights must be non-negative")
            if sum(self.private_weights[k] for k in ('a','b','c')) == 0:
                raise ValueError("Sum of private_weights must be > 0")
            srtd = {cls: self.private_weights[cls] for cls in sorted(self.private_weights.keys())}
            self.private_weights = srtd


class IPGenerator:
    def __init__(self, config: IPConfig):
        self.config = config
        self.rng = random.Random(self.config.seed)

        self.fake = Faker()
        if self.config.seed is not None:
            self.fake.seed_instance(self.config.seed)
        self.priv_classes, self.weights = zip(*self.config.private_weights.items())

    def _priv_class(self):
        return self.rng.choices(self.priv_classes, weights=self.weights, k=1)[0]

    def single(self):
        if self.rng.random() > self.config.public_share:
            cls = self._priv_class()
            return self.fake.ipv4_private(address_class=cls)
        else:
            return self.fake.ipv4_public()

    def batch(self, n):
        if n <= 0:
            raise ValueError("n must be positive")
        return [self.single() for _ in range(n)]
