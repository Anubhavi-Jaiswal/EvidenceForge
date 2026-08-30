def transform(value: str) -> str:
    return value.strip().lower()

import os
def deploy(value):
    os.system(value)
