# -*- coding: utf-8 -*-
"""
검색 키워드로 뉴스 기사 10개 크롤링 후 제목, 요약, 핵심키워드 추출
"""
import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional

import requests
from bs4 import BeautifulSoup

# 요약/키워드는 summarizer 모듈에서 (선택 사용)
def _summarize(text: str, max_sent: int = 3):
    try:
        from summarizer import summarize_text
        return summarize_text(text, max_sentences=max_sent)
    except Exception:
        return None

def _keywords(text: str, top_n: int = 5):
    try:
        from summarizer import extract_keywords
        return extract_keywords(text, top_n=top_n)
    except Exception:
        return []


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
REQUEST_HEADERS = {"User-Agent": USER_AGENT, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"}


@dataclass
class NewsArticle:
    """단일 뉴스 기사"""
    title: str
    url: str
    summary: str
    keywords: list[str] = field(default_factory=list)
    source: str = ""
    raw_text: str = ""


def _fetch_html(url: str, timeout: int = 10) -> Optional[str]:
    try:
        r = requests.get(url, headers=REQUEST_HEADERS, timeout=timeout)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or "utf-8"
        return r.text
    except Exception:
        return None


def _get_article_text(soup: BeautifulSoup) -> str:
    """기사 본문 추출 (일반적인 뉴스 사이트 패턴)"""
    # 제거할 태그
    for tag in soup.find_all(["script", "style", "nav", "footer", "aside", "form"]):
        tag.decompose()
    # 본문 후보: article, .article-body, .content, .post-content, #articleBody 등
    for selector in ["article", "[itemprop='articleBody']", ".article_body", ".news_body",
                     ".content-body", ".post-content", ".article-content", "#articleBody",
                     ".article-view", ".news_view", ".news_ct", "#newsct_article"]:
        body = soup.select_one(selector)
        if body:
            text = body.get_text(separator="\n", strip=True)
            text = re.sub(r"\n{3,}", "\n\n", text)
            if len(text) > 100:
                return text[:5000]
    # fallback: p 태그들
    paragraphs = soup.find_all("p", limit=30)
    if paragraphs:
        text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        if len(text) > 80:
            return text[:5000]
    return ""


def _get_title(soup: BeautifulSoup, url: str) -> str:
    """기사 제목 추출"""
    for tag in ["h1", "[property='og:title']", "title"]:
        if tag.startswith("["):
            el = soup.select_one(tag)
            if el and el.get("content"):
                return el["content"].strip()
            if el:
                return el.get_text(strip=True)[:200]
        el = soup.find(tag)
        if el:
            if el.name == "meta" and el.get("content"):
                return el["content"].strip()[:200]
            text = el.get_text(strip=True)
            if text and len(text) > 5 and len(text) < 300:
                return text[:200]
    return "제목 없음"


def _get_meta_description(soup: BeautifulSoup) -> str:
    """메타 디스크립션으로 요약 후보 확보"""
    for selector in ["meta[name='description']", "meta[property='og:description']"]:
        el = soup.select_one(selector)
        if el and el.get("content"):
            return el["content"].strip()[:500]
    return ""


def _build_summary(soup: BeautifulSoup, body_text: str, title: str) -> str:
    """요약문 생성: 메타 설명 우선, 없으면 본문 앞부분 또는 summarizer 사용"""
    meta = _get_meta_description(soup)
    if meta and len(meta) > 30:
        return meta[:400]
    if body_text and len(body_text) > 50:
        s = _summarize(body_text, 3)
        if s:
            return s[:400]
        return body_text[:400].rsplit(".", 1)[0] + "." if "." in body_text[:400] else body_text[:400]
    return title or "요약 없음"


def fetch_news_urls(query: str, max_items: int = 10) -> list[tuple[str, str, str]]:
    """
    Google News RSS 또는 뉴스 검색에서 기사 URL 수집.
    Returns: [(title, url, source), ...]
    """
    results: list[tuple[str, str, str]] = []
    encoded = urllib.parse.quote_plus(query)

    # 1) Google News RSS 시도 (일부 지역에서 동작)
    rss_url = f"https://news.google.com/rss/search?q={encoded}&hl=ko&gl=KR&ceid=KR:ko"
    try:
        import feedparser
        feed = feedparser.parse(rss_url, request_headers=REQUEST_HEADERS)
        for e in feed.entries[:max_items]:
            link = e.get("link") or (e.get("links") or [{}])[0].get("href")
            if link:
                results.append((e.get("title", "")[:200], link, e.get("source", {}).get("title", "")))
        if len(results) >= max_items:
            return results[:max_items]
    except Exception:
        pass

    # 2) Google News HTML 검색 결과 파싱 (RSS 실패 시)
    search_url = f"https://news.google.com/search?q={encoded}&hl=ko&gl=KR&ceid=KR:ko"
    html = _fetch_html(search_url)
    if html:
        soup = BeautifulSoup(html, "lxml")
        for a in soup.select('a[href^="./articles/"]')[:max_items]:
            href = a.get("href") or ""
            if href.startswith("./"):
                href = "https://news.google.com/" + href[2:]
            title_el = a.select_one("h3") or a
            title_text = title_el.get_text(strip=True)[:200] if title_el else ""
            if href and title_text:
                results.append((title_text, href, "Google News"))
            if len(results) >= max_items:
                break

    return results[:max_items]


def crawl_articles(query: str, max_articles: int = 10) -> list[NewsArticle]:
    """
    검색 키워드로 뉴스 10개 크롤링 후 각 기사별 제목, 요약, 핵심키워드 반환.
    """
    url_tuples = fetch_news_urls(query, max_items=max_articles)
    articles: list[NewsArticle] = []

    for title_from_rss, url, source in url_tuples:
        html = _fetch_html(url)
        if not html:
            articles.append(NewsArticle(
                title=title_from_rss or "로드 실패",
                url=url,
                summary="본문을 불러오지 못했습니다.",
                keywords=[],
                source=source,
            ))
            continue

        soup = BeautifulSoup(html, "lxml")
        title = _get_title(soup, url) or title_from_rss
        body_text = _get_article_text(soup)
        summary = _build_summary(soup, body_text, title)

        keywords: list[str] = _keywords(title + "\n" + (body_text or ""), 5)
        if not keywords and body_text:
            # 간단한 fallback: 2글자 이상 단어 빈도
            from collections import Counter
            words = re.findall(r"[가-힣a-zA-Z]{2,}", body_text + " " + title)
            stop = {"있다", "하다", "된다", "그리고", "그러나", "이번", "통해", "대해", "위해", "있는", "있는", "없는"}
            keywords = [w for w, _ in Counter(words).most_common(15) if w not in stop][:5]

        articles.append(NewsArticle(
            title=title,
            url=url,
            summary=summary,
            keywords=keywords,
            source=source,
            raw_text=body_text[:3000],
        ))

    return articles
