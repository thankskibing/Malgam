from openai import OpenAI
import streamlit as st
from pathlib import Path
import base64
from itertools import zip_longest

# ================= 기본 =================
st.set_page_config(page_title="말감 챗봇", page_icon="🥔", layout="centered")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ================= 유틸 =================
def logo_tag(path="logo.png"):
    p = Path(path)
    if not p.exists():
        for c in [Path("static")/path, Path("assets")/path, Path("app/static")/path]:
            if c.exists():
                p = c
                break
    if not p.exists():
        return '<span class="logo-missing"></span>'
    data = base64.b64encode(p.read_bytes()).decode()
    ext = (p.suffix[1:] or "png")
    return f'<img src="data:image/{ext};base64,{data}" alt="logo" />'

# ================= 스타일 =================
st.markdown("""
<style>
:root{
  --chat-input-h: 64px;  /* 데스크톱 입력창 높이 추정 */
}

/* 헤더 숨기기 + 배경 */
[data-testid="stHeader"]{display:none;}
.stApp{background:linear-gradient(180deg,#7B2BFF 0%,#8A39FF 35%,#A04DFF 100%)!important;}
.block-container{padding-top:0!important; padding-bottom: calc(var(--chat-input-h) + 20px) !important}

/* 상단바 */
.topbar{display:flex;align-items:center;gap:12px;padding:20px 16px 8px}
.topbar h1{color:#fff;margin:0;font-size:28px;line-height:1}
.topbar img{height:40px;max-width:120px;width:auto;object-fit:contain;}
@media (max-width:480px){ .topbar img{height:28px;max-width:90px;} }

/* 카드 */
.chat-card{background:#fff;border-radius:24px;box-shadow:0 12px 40px rgba(0,0,0,.12);padding:16px 16px 8px;margin:8px 12px 24px}

/* 말풍선 */
.chat-bubble{display:block;clear:both;max-width:80%;padding:12px 16px;border-radius:16px;margin:12px 0;line-height:1.45;white-space:pre-wrap;word-break:break-word}
.user-bubble{background:#DCF8C6;float:right;text-align:right}
.assistant-bubble{background:#F1F0F0;float:left;text-align:left}

/* 스피너(흰색) */
[data-testid="stSpinner"], [data-testid="stSpinner"] * {color:#FFFFFF !important;}
[data-testid="stSpinner"] svg circle{stroke:#FFFFFF !important;}
[data-testid="stSpinner"] svg path{stroke:#FFFFFF !important; fill:#FFFFFF !important;}

/* 입력창: 하단 고정(겹침 방지 위해 최상단 z-index) */
[data-testid="stChatInput"]{
  position: fixed; left: 0; right: 0; bottom: 0;
  z-index: 2147483647;
  background:#F5F1FF!important;border-radius:999px!important;border:1px solid #E0CCFF!important;
  box-shadow:0 -2px 8px rgba(123,43,255,.15)!important;padding:6px 12px!important
}
[data-testid="stChatInput"] textarea,[data-testid="stChatInput"] input,[data-testid="stChatInput"] div[contenteditable="true"]{border:none!important;outline:none!important;box-shadow:none!important;background:transparent!important}
[data-testid="stChatInput"] button svg path{fill:#7B2BFF!important}

/* 퀵버튼(스트림릿 버튼) pill 스타일 */
div.quickchips { margin: 0 12px 12px 12px; padding: 12px; border-radius: 16px;
  background: linear-gradient(180deg,#7B2BFF 0%,#8A39FF 60%,#A04DFF 100%); box-shadow: 0 -4px 12px rgba(0,0,0,.15);}
div.quickchips h4 { color:#fff; margin: 0 0 10px 4px; }
div.quickchips .stButton>button{
  width: 100%; border: 1px solid #7B2BFF; background: #fff; color:#1F55A4;
  font-weight: 800; border-radius: 999px; padding: 8px 12px; box-shadow: 0 2px 6px rgba(0,0,0,.08);
}
div.quickchips .stButton>button:hover{ background:#F5F1FF }
</style>
""", unsafe_allow_html=True)

# ================= 상단바 =================
st.markdown(f'<div class="topbar">{logo_tag("logo.png")}<h1>말감 챗봇</h1></div>', unsafe_allow_html=True)

# ================= 세션 =================
SYSTEM = """#지침: 너는 ui/ux 기획, 디자인, 리서처 업무를 도와주는 말감이야.
친근하게 답하고 마지막에 답변에 맞는 이모지 추가. 영어 질문도 한글로 답변."""
WELCOME = "안녕하세요! 저는 여러분을 도와줄 ‘말하는 감자 말감이’예요. 궁금한 점이나 고민이 있다면 자유롭게 물어보라감!😊"

if "messages" not in st.session_state:
    st.session_state.messages = [{"role":"system","content":SYSTEM}]
if "welcome_shown" not in st.session_state:
    st.session_state.welcome_shown = False

# ================= 전송 함수 (완성 후 한 번에 표시; rerun 없음) =================
def send_and_stream(user_text: str):
    st.session_state.messages.append({"role":"user","content":user_text})
    with st.spinner("🥔💭말감이 생각 중…"):
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.messages,
            stream=True,
        )
        chunks = []
        for ch in stream:
            tok = ch.choices[0].delta.content
            if tok:
                chunks.append(tok)
    assistant = "".join(chunks)
    st.session_state.messages.append({"role":"assistant","content":assistant})
    # rerun 호출하지 않음 → 자연스러운 1회 재렌더만 일어남

# ================= 카드 시작 =================
st.markdown('<div class="chat-card">', unsafe_allow_html=True)

# 환영 메시지(최초 1회)
if not st.session_state.welcome_shown:
    st.markdown(f'<div class="chat-bubble assistant-bubble">{WELCOME}</div>', unsafe_allow_html=True)
    st.session_state.welcome_shown = True

# ========= (A) 텍스트 입력 선처리 =========
user_text = st.chat_input("말감이가 질문 기다리는 중!🥔")
if user_text:
    send_and_stream(user_text)

# ========= (B) 퀵버튼 선처리 (URL 파라미터 X, 네이티브 버튼) =========
chips = [
  "👥UX 리서치 설계","📝AI 기획서 작성","🛠️툴 추천",
  "💬프롬프트 가이드","🎨피그마 사용법","📄노션 사용법"
]

# 퀵버튼을 입력창 ‘바로 위’에 배치 (고정 아님)
with st.container():
    st.markdown('<div class="quickchips"><h4>아래 키워드로 물어보라감</h4>', unsafe_allow_html=True)
    # 3열 그리드로 버튼 만들기
    rows = [chips[i:i+3] for i in range(0, len(chips), 3)]
    for r in rows:
        cols = st.columns(3, vertical_alignment="center")
        for c, label in zip_longest(cols, r, fillvalue=""):
            with c:
                if label and st.button(label, key=f"chip_{label}"):
                    st.session_state["_pending_chip"] = label
    st.markdown('</div>', unsafe_allow_html=True)

# 버튼 클릭은 자연 rerun 1회 발생 → 여기서 처리
if st.session_state.get("_pending_chip"):
    picked = st.session_state.pop("_pending_chip")
    send_and_stream(picked)

# ================= 대화 렌더 =================
for m in st.session_state.messages:
    if m["role"] == "system":
        continue
    cls = "user-bubble" if m["role"] == "user" else "assistant-bubble"
    st.markdown(f'<div class="{cls} chat-bubble">{m["content"]}</div>', unsafe_allow_html=True)

# ================= 카드 종료 =================
st.markdown('</div>', unsafe_allow_html=True)
