# 뉴스 키워드 검색 & 콘텐츠 요약

검색 키워드를 입력하면 관련 뉴스 10개를 수집하고, **제목 / 요약 / 핵심키워드**로 정리합니다.  
핵심키워드를 선택하면 해당 키워드가 포함된 기사만 볼 수 있으며,  
수집한 기사들을 종합해 **핵심 주제**, **1200자 블로그 글**, **200자 내외 스레드**, **인스타 5장 카드뉴스**를 생성합니다.

---

## 🚀 배포 (로컬 없이 실행하기)

로컬에서 `pip`/`python`이 안 되면 **GitHub + Streamlit Cloud**로 앱을 배포해 브라우저에서 바로 사용할 수 있습니다. **Vercel**에는 앱으로 연결하는 랜딩 페이지만 배포합니다.

### 1단계: GitHub 저장소 만들기

1. [GitHub](https://github.com/new)에서 새 저장소 생성 (이름 예: `news-crawler-app`).
2. 로컬 프로젝트 폴더에서:

```bash
git init
git add .
git commit -m "Initial: 뉴스 크롤링 & 콘텐츠 요약 앱"
git branch -M main
git remote add origin https://github.com/본인아이디/저장소이름.git
git push -u origin main
```

(이미 Git 저장소가 있으면 `git add .` → `git commit` → `git push`만 진행하면 됩니다.)

### 2단계: Streamlit Cloud에 앱 배포 (실제 앱 동작)

1. [share.streamlit.io](https://share.streamlit.io) 접속 후 **GitHub로 로그인**.
2. **Deploy an app** → 저장소·브랜치 선택.
3. **Main file path**: `app.py`
4. **Advanced settings** → **Secrets**에 OpenAI 사용 시 예시:
   ```toml
   OPENAI_API_KEY = "sk-..."
   ```
5. **Deploy** 클릭. 빌드 후 `https://xxx.streamlit.app` 형태의 URL이 생성됩니다.
6. 이 URL을 복사해 두었다가 **3단계 Vercel**에서 사용합니다.

### 3단계: Vercel에 랜딩 페이지 배포

1. [vercel.com](https://vercel.com) 로그인 후 **Add New** → **Project**.
2. 같은 GitHub 저장소 선택 후:
   - **Root Directory**를 `web`으로 지정.
   - **Deploy** 실행.
3. 배포가 끝난 뒤 **Settings** → **Environment Variables**에 추가:
   - Name: `STREAMLIT_APP_URL`
   - Value: 2단계에서 복사한 Streamlit 앱 URL (예: `https://xxx.streamlit.app`)
4. **Redeploy** 한 번 하면, Vercel 사이트의 "앱 사용하기" 버튼이 Streamlit 앱으로 연결됩니다.

**요약**: 앱은 **Streamlit Cloud**에서 동작하고, **Vercel**은 그 앱으로 들어가는 입구 페이지 역할을 합니다.

---

## 아웃풋 구성

| 구분 | 설명 |
|------|------|
| **뉴스 목록** | 기사별 제목, 요약, 핵심키워드, 원문 링크 |
| **키워드 필터** | 선택한 핵심키워드가 포함된 기사만 표시 |
| **핵심 주제** | 수집 기사를 종합한 한 가지 핵심 주제 |
| **블로그 글** | 1200자 내외 종합 블로그 포스트 |
| **스레드** | 200자 내외 트위터/스레드용 요약 |
| **인스타 카드뉴스** | 5장 분량 카드별 텍스트 |

---

## 로컬 실행 방법

로컬에서 돌릴 때는 아래 중 편한 방법을 사용하세요.

- **CMD**에서: `py -m pip install -r requirements.txt` → `py -m streamlit run app.py`
- **Anaconda Prompt**에서: `pip install -r requirements.txt` → `streamlit run app.py`
- Windows에서: `install_and_run.bat` 더블클릭 (같은 폴더에 있을 때)

브라우저에서 검색 키워드 입력 후 **「뉴스 수집 및 분석 실행」**을 누르면 됩니다.

---

## 선택 사항

- **키워드 추출**: `keybert`, `sentence-transformers` 설치 시 KeyBERT 사용. 미설치 시 빈도 기반 키워드.
- **종합 콘텐츠**: `OPENAI_API_KEY` 설정 시 GPT로 블로그/스레드/카드뉴스 생성. 미설정 시 요약 기반 템플릿.

Streamlit Cloud에서는 **Secrets**에 `OPENAI_API_KEY`를 넣으면 동일하게 적용됩니다.

---

## 프로젝트 구조

```
Project/
├── app.py                 # Streamlit 앱 진입점
├── crawler.py             # 뉴스 URL 수집 + 기사 크롤링, 제목/요약/키워드
├── summarizer.py          # 요약·키워드 추출 (선택)
├── content_synthesis.py   # 종합 콘텐츠 생성
├── requirements.txt
├── packages.txt           # Streamlit Cloud 시스템 패키지 (선택)
├── .streamlit/
│   └── config.toml
├── web/                   # Vercel 배포용 (랜딩 페이지)
│   ├── index.html
│   ├── vercel.json
│   └── api/
│       └── app-url.js     # STREAMLIT_APP_URL 반환
├── .gitignore
└── README.md
```
