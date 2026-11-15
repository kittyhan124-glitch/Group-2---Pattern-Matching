import csv
import glob
import hashlib
import json
import os
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")


def compute_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(64 * 1024):
            hasher.update(chunk)
    return hasher.hexdigest()


def profile_file(filepath: str):
    filename = os.path.basename(filepath)
    size_bytes = os.path.getsize(filepath)
    sha256_hash = compute_sha256(filepath)

    with open(filepath, "rb") as f:
        data = f.read()

    lines_count = len(data.split(b"\n"))

    distinct_bytes = len(set(data))

    non_ascii_count = sum(1 for b in data if b >= 128)
    non_ascii_ratio = (
        round(non_ascii_count / size_bytes, 4) if size_bytes > 0 else 0.0
    )

    try:
        text = data.decode("utf-8")
        is_valid_utf8 = True
        nfc_stable = unicodedata.normalize("NFC", text) == text
    except UnicodeDecodeError:
        is_valid_utf8 = False
        nfc_stable = False

    manifest_entry = {
        "filename": filename,
        "path": os.path.relpath(filepath, DATA_DIR).replace(os.sep, "/"),
        "size_bytes": size_bytes,
        "sha256": sha256_hash,
    }

    profile_entry = {
        "filename": filename,
        "size_bytes": size_bytes,
        "lines_count": lines_count,
        "distinct_bytes": distinct_bytes,
        "non_ascii_ratio": non_ascii_ratio,
        "is_valid_utf8": is_valid_utf8,
    }

    hash_entry = {
        "file": filename,
        "bytes": size_bytes,
        "sha256": sha256_hash,
        "utf8_valid": int(is_valid_utf8),
        "nfc_stable": int(nfc_stable),
        "distinct_bytes": distinct_bytes,
        "pct_bytes_ge_128": round(100 * non_ascii_ratio, 4),
        "lf_count": data.count(b"\n"),
    }

    return manifest_entry, profile_entry, hash_entry


def main():
    bin_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.bin")))
    if not bin_files:
        print("Không tìm thấy file .bin nào trong thư mục data/")
        return

    manifest_list = []
    profile_list = []
    hash_list = []

    print(f"Đang phân tích {len(bin_files)} file dữ liệu...")
    for fpath in bin_files:
        m_entry, p_entry, h_entry = profile_file(fpath)
        manifest_list.append(m_entry)
        profile_list.append(p_entry)
        hash_list.append(h_entry)
        print(f"Đã xử lý: {p_entry['filename']} (SHA-256: {m_entry['sha256'][:10]}...)")

    with open(os.path.join(DATA_DIR, "corpus_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest_list, f, indent=4, ensure_ascii=False)
    print("\n-> Đã tạo thành công: corpus_manifest.json")

    fieldnames = [
        "filename",
        "size_bytes",
        "lines_count",
        "distinct_bytes",
        "non_ascii_ratio",
        "is_valid_utf8",
    ]
    with open(os.path.join(DATA_DIR, "data_profile.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(profile_list)
    print("-> Đã tạo thành công: data_profile.csv")

    hash_fields = ["file", "bytes", "sha256", "utf8_valid", "nfc_stable", "distinct_bytes",
                   "pct_bytes_ge_128", "lf_count"]
    with open(os.path.join(DATA_DIR, "data_hashes.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=hash_fields)
        writer.writeheader()
        writer.writerows(hash_list)
    print("-> Đã tạo thành công: data_hashes.csv")


if __name__ == "__main__":
    main()