from flask import g
from ..utils.utils import get_value
import random

def get_ab_variant(name):
    variants = g.get('ab_variants', None)
    if variants is None:
        variants = dict()
    
    if name in variants:
        return variants[name]

    variants[name] = 'TEST' if bool(random.getrandbits(1)) else 'CONTROL'
    g.ab_variants = variants
    return variants[name]

def get_all_variants():
    return g.get('ab_variants', {})
