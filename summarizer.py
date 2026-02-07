# -*- coding: utf-8 -*-
"""
한국어 텍스트 요약 및 핵심키워드 추출 (KeyBERT 등 활용)
"""
import re
from typing import List


def summarize_text(text: str, max_sentences: int = 3) -> str:
    """
    본문 요약. sumy 사용 시 추출적 요약, 없으면 앞문장 N개.
    """
    if not text or len(text.strip()) < 50:
        return text.strip()[:400]
    text = text.strip()
    # 문장 단위 분리 (한국어 마침표 등)
    sentences = re.split(r"(?<=[.!?。])\s+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    if not sentences:
        return text[:400]
    try:
        from sumy.nlp.tokenizers import Tokenizer
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.summarizers.text_rank import TextRankSummarizer
        from sumy.nlp.stemmers import Stemmer
        # sumy는 영어 위주이므로 한국어는 앞문장 사용
        lang = "korean" if re.search(r"[가-힣]", text) else "english"
        parser = PlaintextParser.from_string(text, Tokenizer(lang))
        summarizer = TextRankSummarizer()
        summary_sentences = summarizer(parser.document, max_sentences)
        return " ".join(str(s) for s in summary_sentences)[:400]
    except Exception:
        return " ".join(sentences[:max_sentences])[:400]


def extract_keywords(text: str, top_n: int = 5) -> List[str]:
    """
    핵심키워드 추출. KeyBERT multilingual 사용, 없으면 빈 리스트.
    """
    if not text or len(text.strip()) < 20:
        return []
    text = (text or "")[:3000]
    try:
        from keybert import KeyBERT
        kw_model = KeyBERT(model="paraphrase-multilingual-MiniLM-L12-v2")
        keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words="english",
            top_n=top_n,
            use_mmr=True,
            diversity=0.6,
        )
        return [k for k, _ in keywords if k and len(k.strip()) > 0][:top_n]
    except Exception:
        pass
    # fallback: 2글자 이상 한글/영어 빈도
    from collections import Counter
    words = re.findall(r"[가-힣a-zA-Z]{2,}", text)
    stop = {"있다", "하다", "된다", "그리고", "그러나", "이번", "통해", "대해", "위해", "있는", "없는", "같다", "위한"}
    return [w for w, _ in Counter(words).most_common(20) if w not in stop][:top_n]
