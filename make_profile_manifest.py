import csv
import glob
import hashlib
import json
import os


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
        data.decode("utf-8")
        is_valid_utf8 = True
    except UnicodeDecodeError:
        is_valid_utf8 = False

    manifest_entry = {
        "filename": filename,
        "path": filepath,
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

    return manifest_entry, profile_entry


def main():
    bin_files = sorted(glob.glob("data/*.bin"))
    if not bin_files:
        print("Không tìm thấy file .bin nào trong thư mục data/")
        return

    manifest_list = []
    profile_list = []

    print(f"Đang phân tích {len(bin_files)} file dữ liệu...")
    for fpath in bin_files:
        m_entry, p_entry = profile_file(fpath)
        manifest_list.append(m_entry)
        profile_list.append(p_entry)
        print(f"Đã xử lý: {p_entry['filename']} (SHA-256: {m_entry['sha256'][:10]}...)")

    with open("corpus_manifest.json", "w", encoding="utf-8") as f:
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
    with open("data_profile.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(profile_list)
    print("-> Đã tạo thành công: data_profile.csv")


if __name__ == "__main__":
    main()