from openai import OpenAI
import streamlit as st
from pathlib import Path
import base64

# ----------------- 기본 -----------------
st.set_page_config(page_title="말감 챗봇", page_icon="🥔", layout="centered")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ----------------- 로고(Base64 인라인) -----------------
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

# ----------------- 스타일 -----------------
st.markdown("""
<style>
/* 헤더 숨기기 + 배경 */
[data-testid="stHeader"]{display:none;}
.stApp{background:linear-gradient(180deg,#7B2BFF 0%,#8A39FF 35%,#A04DFF 100%)!important;}
.block-container{padding-top:0!important}

/* 상단 바 (로고 + 타이틀) */
.topbar{display:flex;align-items:center;gap:12px;padding:20px 16px 6px}
.topbar h1{color:#fff;margin:0;font-size:28px;line-height:1}
.topbar img{height:40px;max-width:120px;width:auto;object-fit:contain;}
@media (max-width:480px){ .topbar img{height:28px;max-width:90px;} }

/* 타이틀 바로 아래 얇은 라인 */
.top-accent{height:2px;margin:6px 16px 10px 16px;background:rgba(255,255,255,.9);border-radius:999px;}

/* 카드 */
.chat-card{
  background:#fff;border-radius:24px;box-shadow:0 12px 40px rgba(0,0,0,.12);
  padding:14px 16px 6px; margin:6px 12px 8px;
}

/* 말풍선 */
.chat-bubble{display:block;clear:both;max-width:80%;padding:12px 16px;border-radius:16px;margin:10px 0;line-height:1.45;white-space:pre-wrap;word-break:break-word}
.user-bubble{background:#DCF8C6;float:right;text-align:right}
.assistant-bubble{background:#F1F0F0;float:left;text-align:left}

/* ===== 퀵칩(버튼) : 전 해상도 3×3, 간격 10px ===== */
.quick-title{color:#fff;font-weight:700;margin:8px 0 6px 16px}
.chips-wrap{margin:0 16px 16px 16px}
.quick-row{ margin-bottom:10px; }

/* 3열 강제(모바일에서도) + 열 간격 10px */
.quick-row [data-testid="stHorizontalBlock"]{ gap:10px !important; }
.quick-row [data-testid="column"]{
  padding:0 !important;
  flex:0 0 calc((100% - 20px)/3) !important;
  max-width:calc((100% - 20px)/3) !important;
}

/* 칩 버튼 (아이콘+텍스트 여유 있게) */
.quick-btn .stButton>button{
  width:100%; border-radius:100px;
  padding:10px 14px;                               /* 여유 ↑ */
  font-size:clamp(12px, 3.5vw, 13px);              /* 모바일 12 ~ 데스크탑 13 */
  font-weight:800; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
  background:#fff !important; color:#1F55A4 !important; border:1px solid #7B2BFF !important;
  box-shadow:0 2px 6px rgba(0,0,0,.08); transition:background-color .2s, transform .06s;
}
.quick-btn .stButton>button:hover{ background:#F5F1FF !important; }
.quick-btn .stButton>button:active{ transform:scale(.98); }

/* 스피너 흰색 */
[data-testid="stSpinner"], [data-testid="stSpinner"] * {color:#FFFFFF !important;}
[data-testid="stSpinner"] svg circle{stroke:#FFFFFF !important;}
[data-testid="stSpinner"] svg path{stroke:#FFFFFF !important; fill:#FFFFFF !important;}

/* 입력창: 언더라인 스타일(두꺼운 흰 바 제거) */
[data-testid="stChatInput"]{
  background:transparent !important; border:none !important;
  border-bottom:2px solid rgba(255,255,255,.9) !important; border-radius:0 !important;
  box-shadow:none !important; padding:0 12px 6px 12px !important; margin:6px 16px 10px 16px !important;
}
[data-testid="stChatInput"]:focus-within{border-bottom:2px solid #FFFFFF !important; box-shadow:none !important;}
[data-testid="stChatInput"] textarea,[data-testid="stChatInput"] input,[data-testid="stChatInput"] div[contenteditable="true"]{
  background:transparent !important; border:none !important; outline:none !important; box-shadow:none !important;
}
[data-testid="stChatInput"] button svg path{fill:#FFFFFF !important;}
</style>
""", unsafe_allow_html=True)

# ----------------- 상단 바 + 언더라인 -----------------
st.markdown(f'<div class="topbar">{logo_tag("logo.png")}<h1>말감 챗봇</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="top-accent"></div>', unsafe_allow_html=True)

# ----------------- 카드 시작 -----------------
st.markdown('<div class="chat-card">', unsafe_allow_html=True)

# ----------------- 세션 -----------------
SYSTEM = """#지침: 너는 ui/ux 기획, 디자인, 리서처 업무를 도와주고 질문을 받아주는 역할을 하는 말감이야.
말끝은 '요'로, 친근하게 답하고 마지막에 맞는 이모지 추가. 영어 질문도 한글로 답변."""
WELCOME = "안녕하세요! 저는 여러분을 도와줄 ‘말하는 감자 말감이’예요. 궁금한 점이나 고민이 있다면 자유롭게 물어보라감!😊"

if "messages" not in st.session_state:
    st.session_state.messages = [{"role":"system","content":SYSTEM}]
if "welcome_shown" not in st.session_state:
    st.session_state.welcome_shown = False

# ----------------- 응답 함수 -----------------
def send_and_stream(user_text: str):
    st.session_state.messages.append({"role":"user","content":user_text})
    with st.spinner("🥔💭말감이 생각 중…"):
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.messages,
            stream=True,
        )
        assistant = ""
        for ch in stream:
            assistant += ch.choices[0].delta.content or ""
        st.session_state.messages.append({"role":"assistant","content":assistant})

# ========= 1) 환영 말풍선 먼저 =========
if not st.session_state.welcome_shown:
    st.markdown(f'<div class="chat-bubble assistant-bubble">{WELCOME}</div>', unsafe_allow_html=True)
    st.session_state.welcome_shown = True

# ========= 2) 키워드 칩(3×3, 버튼 기반) =========
st.markdown('<div class="quick-title">🥔 아래 키워드 눌러서 물어보라감 🥔</div>', unsafe_allow_html=True)

chips = [
    "📝AI 기획서 작성","🛠️툴 추천","💡아이디어 확장",
    "🔍AI 리서치","🎨피그마 사용법","📄노션 사용법",
    "🖱️프로토타입 팁","👥UX 리서치 설계","💬프롬프트 가이드"
]

for start in range(0, len(chips), 3):
    st.markdown('<div class="chips-wrap"><div class="quick-row">', unsafe_allow_html=True)
    cols = st.columns(3)  # 3열 고정 (CSS로 강제)
    for col, label in zip(cols, chips[start:start+3]):
        with col:
            st.markdown('<div class="quick-btn">', unsafe_allow_html=True)
            if st.button(label, key=f"chip_{start}_{label}", help="클릭하면 바로 전송돼요"):
                send_and_stream(label)   # ✅ 페이지 이동 없음 → 하얀 번쩍임 제거
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

# ========= 3) 대화 렌더 =========
for m in st.session_state.messages:
    if m["role"] == "system":
        continue
    cls = "user-bubble" if m["role"] == "user" else "assistant-bubble"
    st.markdown(f'<div class="{cls} chat-bubble">{m["content"]}</div>', unsafe_allow_html=True)

# ========= 4) 입력창 =========
if txt := st.chat_input("말감이가 질문 기다리는 중!🥔"):
    send_and_stream(txt)

# ----------------- 카드 종료 -----------------
st.markdown('</div>', unsafe_allow_html=True)
