from itertools import islice
from pathlib import Path


def print_first_lines(file_path: str, lines: int = 40):
    path = Path(file_path)

    print("=" * 80)
    print(f"File: {path}")
    print("=" * 80)

    with open(path, "r", encoding="utf-8", errors="ignore") as file:
        print("".join(islice(file, lines)))


print_first_lines("data/unknown/neg/NEG_fbmn.mgf")
print_first_lines("data/unknown/pos/POS_fbmn.mgf")
print_first_lines("data/reference/neg/20241003_enamdisc_neg_ms2.mgf")
print_first_lines("data/reference/pos/20241003_enamdisc_pos_ms2.mgf")