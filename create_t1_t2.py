import os
import unicodedata
from datasets import load_dataset

os.makedirs("data", exist_ok=True)

MIB = 1024 * 1024
TARGET_SIZES = [1, 2, 4, 8, 16]  
MAX_SIZE = 16 * MIB


def make_wikipedia_corpus(lang_code: str, output_name: str):
    dataset_id = f"20231101.{lang_code}"
    print(f"\n--- Đang tải dữ liệu {dataset_id} từ Hugging Face ---")

    ds = load_dataset(
        "wikimedia/wikipedia", dataset_id, split="train", streaming=True
    )

    collected_bytes = bytearray()
    article_count = 0

    for row in ds:
        raw_text = row["text"]
        nfc_text = unicodedata.normalize("NFC", raw_text)
        encoded_bytes = (nfc_text + "\n").encode("utf-8")

        collected_bytes.extend(encoded_bytes)
        article_count += 1

        if len(collected_bytes) >= MAX_SIZE:
            print(f"-> Thu thập đủ dung lượng từ {article_count} bài viết.")
            break

    for size_mib in TARGET_SIZES:
        bytes_needed = size_mib * MIB
        file_path = f"data/{output_name}_{size_mib}MiB.bin"
        data_slice = collected_bytes[:bytes_needed]

        try:
            data_slice.decode("utf-8")
        except UnicodeDecodeError as e:
            data_slice = (
                data_slice[: e.start] + b" " * (bytes_needed - e.start)
            )

        with open(file_path, "wb") as f:
            f.write(data_slice)

        print(f"Đã lưu: {file_path} ({len(data_slice)} bytes)")


if __name__ == "__main__":
    make_wikipedia_corpus("vi", "T1_vi")

    make_wikipedia_corpus("en", "T2_en")