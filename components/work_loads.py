#!/usr/bin/env python3
from .work_loads_modules.url_generator import generate_urls
from .work_loads_modules.en_word_generator import generate_random_words, gen_words_with_prefix_freq
from .work_loads_modules.ip_generator import IPGenerator, IPConfig

class WorkLoad:
    def __init__(self, seed=None):
        self.seed = seed

    def words(self, num_words, p_freq=0, unique=False):
        if p_freq > 0:
            return gen_words_with_prefix_freq(num_words, p_freq, self.seed, unique)
        else:
            return generate_random_words(num_words, self.seed, unique)

    def urls(self, num_urls):
        return generate_urls(num_urls, self.seed)

    def ips(self, num_ips):
        if num_ips <= 0:
            raise ValueError("num_ips must be positive")
        cfg = IPConfig(seed=self.seed)
        gen = IPGenerator(cfg)
        if num_ips == 1:
            return gen.single()
        else:
            return gen.batch(num_ips)
        