# -*- coding: utf-8 -*-
"""
뉴스 기사들을 종합해 핵심 주제, 블로그 글(1200자), 스레드(~200자), 인스타 5장 카드뉴스 생성
"""
import os
from dataclasses import dataclass
from typing import List, Optional

from crawler import NewsArticle


@dataclass
class SynthesizedContent:
    """종합 콘텐츠 아웃풋"""
    core_theme: str
    blog_post: str
    thread_content: str
    instagram_cards: List[str]  # 5장 분량 텍스트


def _build_context(articles: List[NewsArticle], max_chars: int = 8000) -> str:
    """기사 제목+요약으로 컨텍스트 문자열 생성"""
    parts = []
    total = 0
    for i, a in enumerate(articles, 1):
        block = f"[기사{i}] 제목: {a.title}\n요약: {a.summary}\n"
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "\n".join(parts)


def _synthesize_with_openai(articles: List[NewsArticle]) -> Optional[SynthesizedContent]:
    """OpenAI API로 핵심 주제 + 블로그/스레드/카드뉴스 생성 (선택 사항)"""
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY_FILE")
    if api_key and os.path.isfile(api_key):
        with open(api_key) as f:
            api_key = f.read().strip()
    if not api_key:
        return None
    context = _build_context(articles)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        sys = (
            "당신은 뉴스 기사들을 분석해 하나의 핵심 주제를 뽑고, "
            "블로그 글(1200자 내외), 스레드용 짧은 글(200자 내외), "
            "인스타그램 카드뉴스 5장 분량의 문장 5개를 작성하는 전문가입니다. "
            "한국어로만 답하고, JSON 형식으로만 답하세요."
        )
        user = (
            "아래 뉴스 기사들(제목+요약)을 분석해서 다음 JSON만 출력해줘. "
            "다른 설명 없이 JSON만.\n\n"
            "{\n"
            '  "core_theme": "핵심 주제 한 문장",\n'
            '  "blog_post": "1200자 내외 블로그 글 전체",\n'
            '  "thread_content": "200자 내외 스레드/트윗용 요약",\n'
            '  "instagram_cards": ["1장 텍스트", "2장 텍스트", "3장 텍스트", "4장 텍스트", "5장 텍스트"]\n'
            "}\n\n"
            "--- 기사 목록 ---\n" + context
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
            temperature=0.6,
        )
        import json
        content = resp.choices[0].message.content
        # JSON 블록만 추출
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            data = json.loads(content[start:end])
            return SynthesizedContent(
                core_theme=data.get("core_theme", ""),
                blog_post=data.get("blog_post", ""),
                thread_content=data.get("thread_content", ""),
                instagram_cards=data.get("instagram_cards", [])[:5],
            )
    except Exception:
        pass
    return None


def synthesize(articles: List[NewsArticle]) -> SynthesizedContent:
    """
    뉴스 기사들을 종합해 핵심 주제, 블로그(1200자), 스레드(200자), 인스타 5장 카드뉴스 생성.
    OPENAI_API_KEY가 있으면 GPT 활용, 없으면 템플릿 기반으로 생성.
    """
    if not articles:
        return SynthesizedContent(
            core_theme="분석할 기사가 없습니다.",
            blog_post="",
            thread_content="",
            instagram_cards=[],
        )

    result = _synthesize_with_openai(articles)
    if result:
        return result

    # 템플릿 기반 (API 없을 때) – 실제 기사 제목·요약 반영
    titles = [a.title.strip() for a in articles if a.title.strip()][:5]
    summaries = [a.summary.strip() for a in articles if a.summary and a.summary.strip()][:5]
    all_keywords = []
    for a in articles:
        all_keywords.extend(k for k in a.keywords if k and k.strip())
    unique_kw = list(dict.fromkeys(all_keywords))[:8]
    theme_kw = ", ".join(unique_kw[:3]) if unique_kw else (titles[0][:30] if titles else "뉴스")

    core_theme = f"종합된 핵심 주제: {theme_kw} 관련 최근 동향과 이슈"

    blog_parts = [f"# {core_theme}\n", "최근 뉴스들을 정리하면 다음과 같습니다.\n"]
    for i, t in enumerate(titles):
        s = summaries[i] if i < len(summaries) else ""
        blog_parts.append(f"## {t}\n{s}\n" if s else f"## {t}\n")
    if summaries:
        blog_parts.append("\n위 기사들을 종합하면, " + (summaries[0][:300] if summaries[0] else "") + " …")
    blog_parts.append("\n\n※ OPENAI_API_KEY를 설정하면 1200자 분량의 블로그 글이 자동 생성됩니다.")
    blog_post = "".join(blog_parts)[:1250]

    thread_parts = [f"📌 {core_theme}\n"]
    if summaries and summaries[0]:
        thread_parts.append(summaries[0][:180])
    thread_parts.append("\n\n※ API 키 설정 시 200자 내외 스레드 문구가 자동 생성됩니다.")
    thread_content = "".join(thread_parts)[:250]

    cards = [
        f"카드 1: {core_theme}",
        f"카드 2: {titles[0][:80]}" if titles else "카드 2: (기사 제목)",
        f"카드 3: {(summaries[0][:80] if summaries else '') or '(요약)'}",
        f"카드 4: 핵심 키워드 – {', '.join(unique_kw[:5]) or '-'}",
        "카드 5: 자세한 내용은 원문 링크에서 확인하세요.",
    ]
    return SynthesizedContent(
        core_theme=core_theme,
        blog_post=blog_post,
        thread_content=thread_content,
        instagram_cards=cards,
    )
