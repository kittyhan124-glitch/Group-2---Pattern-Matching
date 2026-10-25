import os
import random

os.makedirs("data", exist_ok=True)
MIB = 1024 * 1024

seeds = [11, 29, 47]
sizes_rq1 = [1, 2, 4, 8, 16]
alphabet_26 = b"abcdefghijklmnopqrstuvwxyz"

print("--- Đang sinh T3 cho RQ1 ---")
for seed in seeds:
    random.seed(seed)
    for s in sizes_rq1:
        target_bytes = s * MIB
        file_path = f"data/T3_sigma26_{s}MiB_seed{seed}.bin"
        
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
    file_path = f"data/T3_sigma{sigma}_4MiB.bin"
    
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
file_path = "data/T4_worst_4MiB.bin"
with open(file_path, "wb") as f:
    f.write(b"a" * target_bytes)
print(f"Đã lưu: {file_path} ({target_bytes} bytes)")