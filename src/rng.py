import random

class RNG:
    def __init__(self, seed=None):
        if seed is None:
            seed = random.getrandbits(32)
        self.seed = seed
        self._random = random.Random(seed)

    def randint(self, a, b):
        return self._random.randint(a, b)

    def choice(self, seq):
        return self._random.choice(seq)

    def shuffle(self, seq):
        self._random.shuffle(seq)