# -*- coding: utf-8 -*-
"""
뉴스 크롤링 + 키워드 필터 + 종합 콘텐츠(블로그/스레드/카드뉴스) Streamlit 앱
"""
import streamlit as st

from crawler import crawl_articles, NewsArticle
from content_synthesis import synthesize, SynthesizedContent


def collect_all_keywords(articles: list[NewsArticle]) -> list[str]:
    seen = set()
    out = []
    for a in articles:
        for k in a.keywords:
            k = k.strip()
            if k and k not in seen:
                seen.add(k)
                out.append(k)
    return sorted(out)


def filter_articles_by_keyword(articles: list[NewsArticle], selected: list[str]) -> list[NewsArticle]:
    if not selected:
        return articles
    selected_set = set(selected)
    return [a for a in articles if selected_set & set(a.keywords)]


def main():
    st.set_page_config(page_title="뉴스 크롤링 & 콘텐츠 요약", layout="wide")
    st.title("🔍 뉴스 키워드 검색 & 콘텐츠 요약")

    query = st.text_input("검색 키워드", placeholder="예: 인공지능 규제")
    max_articles = st.slider("수집 기사 수", min_value=5, max_value=10, value=10)

    if not query.strip():
        st.info("검색 키워드를 입력한 뒤 실행하세요.")
        return

    if st.button("뉴스 수집 및 분석 실행"):
        with st.spinner("뉴스 수집 및 요약·키워드 추출 중..."):
            articles = crawl_articles(query.strip(), max_articles=max_articles)
            st.session_state["articles"] = articles
            st.session_state["synthesized"] = None

    articles: list[NewsArticle] = st.session_state.get("articles") or []

    if not articles:
        st.stop()

    all_keywords = collect_all_keywords(articles)
    selected_keywords = st.multiselect(
        "핵심키워드로 필터 (선택한 키워드가 포함된 기사만 표시)",
        options=all_keywords,
        default=[],
        key="keyword_filter",
    )
    filtered = filter_articles_by_keyword(articles, selected_keywords)

    st.subheader(f"📰 뉴스 기사 ({len(filtered)}건)")
    for i, a in enumerate(filtered, 1):
        title_display = a.title[:80] + ("..." if len(a.title) > 80 else "")
        with st.expander(f"{i}. {title_display}"):
            summary_display = a.summary if (a.summary and a.summary.strip()) else "(요약 없음 – 아래 링크에서 원문 확인)"
            st.markdown("**요약**")
            st.write(summary_display)
            kw_display = ", ".join(a.keywords) if a.keywords else "추출된 키워드 없음"
            st.caption(f"핵심키워드: {kw_display}")
            st.link_button("기사 보기", a.url)

    st.divider()
    st.subheader("📋 종합 콘텐츠")
    st.caption("수집한 기사를 바탕으로 핵심 주제, 블로그 글, 스레드, 카드뉴스 초안을 생성합니다.")

    if st.session_state.get("synthesized") is None:
        if st.button("종합 콘텐츠 생성 (핵심 주제 + 블로그/스레드/카드뉴스)"):
            with st.spinner("종합 분석 중..."):
                syn = synthesize(articles)
                st.session_state["synthesized"] = syn
        else:
            st.info("👆 위 버튼을 누르면 핵심 주제, 블로그 글(1200자 내외), 스레드(200자 내외), 인스타 카드뉴스 5장이 생성됩니다.")

    syn: SynthesizedContent | None = st.session_state.get("synthesized")
    if syn:
        st.markdown("---")
        st.markdown("#### 🎯 핵심 주제")
        st.info(syn.core_theme)

        st.markdown("#### 📝 블로그 글 (1200자 내외)")
        st.text_area("블로그 글", value=syn.blog_post, height=320, disabled=True, key="blog", label_visibility="collapsed")
        st.caption(f"글자 수: {len(syn.blog_post)}자")

        st.markdown("#### 🧵 스레드/트윗 (200자 내외)")
        st.text_area("스레드", value=syn.thread_content, height=120, disabled=True, key="thread", label_visibility="collapsed")
        st.caption(f"글자 수: {len(syn.thread_content)}자")

        st.markdown("#### 📱 인스타그램 카드뉴스 (5장)")
        for idx, card_text in enumerate(syn.instagram_cards, 1):
            st.markdown(f"**카드 {idx}**")
            st.write(card_text)
            st.write("---")


if __name__ == "__main__":
    main()
