"""ac_fail.py
----------

Cấu trúc gồm 3 thành phần chính:
1. Trie (Tập cây tiền tố): Chuyển trạng thái dựa trên bảng ánh xạ dictionary các byte (0..255).
2. Failure Link: Liên kết nhảy khi gặp mismatch, xây dựng bằng giải thuật BFS (Breadth-First Search).
3. Output Link (Dictionary Suffix Link): Đường tắt trỏ trực tiếp đến nút terminal gần nhất
   trong chuỗi failure link. Nhờ đó, việc thu thập tất cả các kết quả trùng khớp chồng lấn
   (overlapping matches / suffix matches) chỉ tốn O(Z) thời gian, không duyệt thừa.
"""

from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
import unicodedata


@dataclass(frozen=True)
class KeywordItem:

    pid: int
    raw_text: str
    norm_text: str
    byte_pattern: bytes
    byte_len: int


@dataclass
class MatchResult:

    start: int
    end: int
    pid: int
    pattern: bytes


class State:

    __slots__ = ("state_id", "depth", "children", "fail", "output_link", "matches")

    def __init__(self, state_id: int, depth: int = 0):
        self.state_id: int = state_id              
        self.depth: int = depth                    
        self.children: Dict[int, State] = {}       
        self.fail: Optional[State] = None          
        self.output_link: Optional[State] = None   
        self.matches: List[Tuple[int, int, bytes]] = []

    @property
    def is_terminal(self) -> bool:
        return len(self.matches) > 0


def _normalize_keywords(raw_keywords: Union[List[str], List[bytes], List[KeywordItem]]) -> List[KeywordItem]:

    manifest: List[KeywordItem] = []
    seen_bytes = set()
    current_pid = 0

    for item in raw_keywords:
        if hasattr(item, "byte_pattern"):
            if len(item.byte_pattern) == 0:
                raise ValueError("Từ khóa byte không được rỗng!")
            if item.byte_pattern not in seen_bytes:
                seen_bytes.add(item.byte_pattern)
                manifest.append(KeywordItem(
                    pid=getattr(item, "pid", current_pid),
                    raw_text=getattr(item, "raw_text", str(item.byte_pattern)),
                    norm_text=getattr(item, "norm_text", str(item.byte_pattern)),
                    byte_pattern=item.byte_pattern,
                    byte_len=len(item.byte_pattern)
                ))
                current_pid += 1
            continue

        if isinstance(item, (bytes, bytearray)):
            byte_pat = bytes(item)
            if len(byte_pat) == 0:
                raise ValueError("Pattern không được rỗng!")
            if byte_pat in seen_bytes:
                continue
            seen_bytes.add(byte_pat)
            try:
                raw_str = byte_pat.decode("utf-8")
            except UnicodeDecodeError:
                raw_str = str(byte_pat)
            manifest.append(KeywordItem(
                pid=current_pid,
                raw_text=raw_str,
                norm_text=raw_str,
                byte_pattern=byte_pat,
                byte_len=len(byte_pat)
            ))
            current_pid += 1
            continue

        if isinstance(item, str):
            if len(item) == 0:
                raise ValueError("Từ khóa không được là chuỗi rỗng!")
            norm_str = unicodedata.normalize("NFC", item)
            byte_pat = norm_str.encode("utf-8")
            if len(byte_pat) == 0:
                raise ValueError("Từ khóa byte không được rỗng!")
            if byte_pat in seen_bytes:
                continue
            seen_bytes.add(byte_pat)
            manifest.append(KeywordItem(
                pid=current_pid,
                raw_text=item,
                norm_text=norm_str,
                byte_pattern=byte_pat,
                byte_len=len(byte_pat)
            ))
            current_pid += 1
            continue

        raise TypeError(f"Kiểu dữ liệu từ khóa không được hỗ trợ: {type(item)}")

    if not manifest:
        raise ValueError("Danh sách từ khóa không được rỗng!")
    return manifest


class AhoCorasickFail:

    def __init__(self, keywords: Union[List[str], List[bytes], List[KeywordItem], bytes]):

        if isinstance(keywords, (bytes, bytearray)):
            keywords = [bytes(keywords)]

        if not keywords:
            raise ValueError("Danh sách từ khóa không được rỗng!")

        self.manifest: List[KeywordItem] = _normalize_keywords(keywords)
        self.root: State = State(state_id=0, depth=0)
        self.num_states: int = 1  # Bắt đầu từ 1 (root)
        self.total_pattern_length: int = sum(item.byte_len for item in self.manifest)

        self._build_trie()

        self._build_failure_and_output_links()

    def _build_trie(self) -> None:

        for item in self.manifest:
            curr = self.root
            for b in item.byte_pattern:
                if b not in curr.children:
                    new_state = State(state_id=self.num_states, depth=curr.depth + 1)
                    curr.children[b] = new_state
                    self.num_states += 1
                curr = curr.children[b]

            curr.matches.append((item.pid, item.byte_len, item.byte_pattern))

    def _build_failure_and_output_links(self) -> None:

        queue: deque[State] = deque()

        for b, child in self.root.children.items():
            child.fail = self.root       
            child.output_link = None     
            queue.append(child)


        while queue:
            curr = queue.popleft()

            for b, child in curr.children.items():
                queue.append(child)

                f = curr.fail
                while f is not None and b not in f.children:
                    f = f.fail

                if f is not None:
                    child.fail = f.children[b]
                else:
                    child.fail = self.root

                # Tránh tự trỏ failure về chính nó
                if child.fail is child:
                    child.fail = self.root

                if child.fail.is_terminal:
                    child.output_link = child.fail
                else:
                    child.output_link = child.fail.output_link

    def search(self, text_bytes: bytes) -> List[MatchResult]:

        if not isinstance(text_bytes, (bytes, bytearray)):
            raise TypeError("Văn bản tìm kiếm phải ở định dạng byte (bytes hoặc bytearray)!")

        matches: List[MatchResult] = []
        curr = self.root

        for idx, b in enumerate(text_bytes):

            while curr is not None and b not in curr.children:
                curr = curr.fail

            if curr is not None:
                curr = curr.children[b]
            else:
                curr = self.root

            temp: Optional[State] = curr
            while temp is not None:
                if temp.is_terminal:
                    for pid, byte_len, pattern in temp.matches:
                        start_pos = idx - byte_len + 1
                        end_pos = idx + 1
                        matches.append(MatchResult(
                            start=start_pos,
                            end=end_pos,
                            pid=pid,
                            pattern=pattern
                        ))
                temp = temp.output_link

        return matches

    def search_first_hit_per_line(self, line_bytes: bytes) -> Optional[Tuple[int, bytes]]:
        curr = self.root
        for b in line_bytes:
            while curr is not None and b not in curr.children:
                curr = curr.fail

            if curr is not None:
                curr = curr.children[b]
            else:
                curr = self.root

            if curr.is_terminal:
                pid, _, pattern = curr.matches[0]
                return pid, pattern
            if curr.output_link is not None:
                pid, _, pattern = curr.output_link.matches[0]
                return pid, pattern

        return None

    def get_stats(self) -> Dict[str, Union[int, float]]:
        """Trả về các thông số cấu trúc của Automaton phục vụ báo cáo IEEE."""
        return {
            "num_keywords_k": len(self.manifest),
            "num_states_Q": self.num_states,
            "total_pattern_length_L": self.total_pattern_length,
            "avg_pattern_len": self.total_pattern_length / len(self.manifest) if self.manifest else 0
        }

def build(patterns: Union[List[bytes], List[str], bytes, bytearray]) -> AhoCorasickFail:
    """Hàm build theo giao diện chuẩn chung: nhận mẫu và trả về cấu trúc AhoCorasickFail."""
    if isinstance(patterns, (bytes, bytearray)):
        patterns = [bytes(patterns)]
    return AhoCorasickFail(patterns)


def scan(text_bytes: bytes, structure: AhoCorasickFail) -> List[Tuple[int, int]]:
    """Hàm scan theo giao diện chuẩn chung: trả về [(pos, pid), ...] đã sắp xếp."""
    matches = structure.search(text_bytes)
    return [(m.start, m.pid) for m in matches]


def compute_checksum(matches: List[Tuple[int, int]]) -> int:
    """
    Tính mã băm tổng kiểm tra (checksum) theo Mục 5 của hướng dẫn CSD203:
    check = (check + (pos + 1) * 1000003 + pid) % (2**64)
    """
    check = 0
    mod = 1 << 64
    for pos, pid in matches:
        check = (check + (pos + 1) * 1000003 + pid) % mod
    return check


AhoCorasick = AhoCorasickFail


if __name__ == "__main__":
    print("--- Chạy thử nghiệm ac_fail.py ---")
    raw_patterns = ["bác", "bác sĩ", "sĩ", "khám"]
    ac = AhoCorasickFail(raw_patterns)
    stats = ac.get_stats()
    print(f"Thống kê Automaton: {stats}")

    text = "Bác sĩ khám bệnh tại phòng khám bác sĩ"
    text_nfc = unicodedata.normalize("NFC", text.lower())
    text_b = text_nfc.encode("utf-8")

    hits = ac.search(text_b)
    print(f"\nVăn bản byte: {text_b}")
    print(f"Tổng số hits phát hiện (bao gồm chồng lấn): {len(hits)}")
    for hit in hits:
        matched_str = hit.pattern.decode("utf-8")
        print(f"  -> [{hit.start}:{hit.end}] pid={hit.pid}: '{matched_str}'")

    m = build([b"bac", b"si"])
    res = scan(b"bac si", m)
    chk = compute_checksum(res)
    print(f"Giao diện chuẩn build/scan kết quả: {res}, checksum={chk}")
