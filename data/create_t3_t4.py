import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)
MIB = 1024 * 1024

seeds = [11, 29, 47]
sizes_rq1 = [1, 2, 4, 8, 16]
alphabet_26 = b"abcdefghijklmnopqrstuvwxyz"

print("--- Đang sinh T3 cho RQ1 ---")
for seed in seeds:
    for s in sizes_rq1:
        # Keep each size independent so a sample cut from 1 MiB is not
        # deliberately replicated as a prefix in every larger corpus.
        random.seed(seed * 1_000_003 + s)
        target_bytes = s * MIB
        file_path = os.path.join(DATA_DIR, f"T3_sigma26_{s}MiB_seed{seed}.bin")
        
        chunk_size = 64 * 1024
        generated = 0
        with open(file_path, "wb") as f:
            while generated < target_bytes:
                cur = min(chunk_size, target_bytes - generated)
                f.write(bytes(random.choices(alphabet_26, k=cur)))
                generated += cur
        print(f"Đã lưu: {file_path}")

print("\n--- Đang sinh T3 cho RQ2 A ---")
alphabets = {
    2: b"ab",
    4: b"abcd",
    256: bytes(range(256))
}

for sigma, alpha in alphabets.items():
    random.seed(42)  
    target_bytes = 4 * MIB
    file_path = os.path.join(DATA_DIR, f"T3_sigma{sigma}_4MiB.bin")
    
    chunk_size = 64 * 1024
    generated = 0
    with open(file_path, "wb") as f:
        while generated < target_bytes:
            cur = min(chunk_size, target_bytes - generated)
            f.write(bytes(random.choices(alpha, k=cur)))
            generated += cur
    print(f"Đã lưu: {file_path}")

print("\n--- Đang sinh T4 cho RQ2 B ---")
target_bytes = 4 * MIB
file_path = os.path.join(DATA_DIR, "T4_worst_4MiB.bin")
with open(file_path, "wb") as f:
    f.write(b"a" * target_bytes)
print(f"Đã lưu: {file_path} ({target_bytes} bytes)")