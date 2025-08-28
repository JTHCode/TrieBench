import random
from faker import Faker

## === Knobs === ##
public_share = 0.50
priv_weights = {
    'c': 0.55,  # (home/smb gear) → 192.168.x.x
    'a': 0.35,  # (cloud/VPC/enterprise) → 10.x.x.x
    'b': 0.10  # (less common) → 172.16-31.x.x
}
