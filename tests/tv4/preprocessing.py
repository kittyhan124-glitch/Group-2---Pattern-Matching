"""Explicit NFC and canonical pattern IDs before cross-algorithm comparison."""
from dataclasses import dataclass
import unicodedata


def normalize_text(text):
    if not isinstance(text,str):
        raise TypeError('Unicode text must be str')
    return unicodedata.normalize('NFC',text).encode('utf-8')


@dataclass(frozen=True)
class PreparedKeywords:
    patterns:tuple[bytes,...]
    source_to_pid:tuple[int,...]
    raw_keywords:tuple[str,...]
    normalized_keywords:tuple[str,...]
    duplicates_removed:int


def prepare_keywords(keywords):
    if isinstance(keywords,(str,bytes,bytearray)):
        raise TypeError('keywords must be an iterable of strings')
    raw=tuple(keywords)
    if not raw:
        raise ValueError('keyword set must not be empty')
    patterns=[]
    normalized=[]
    mapping=[]
    seen={}
    for word in raw:
        encoded=normalize_text(word)
        if not encoded:
            raise ValueError('keyword must not be empty')
        if b'\n' in encoded:
            raise ValueError('main keyword set must not contain LF')
        if encoded not in seen:
            seen[encoded]=len(patterns)
            patterns.append(encoded)
            normalized.append(encoded.decode('utf-8'))
        mapping.append(seen[encoded])
    return PreparedKeywords(tuple(patterns),tuple(mapping),raw,tuple(normalized),len(raw)-len(patterns))
