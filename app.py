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
                p = c; break
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
.topbar{display:flex;align-items:center;gap:12px;padding:20px 16px 8px}
.topbar h1{color:#fff;margin:0;font-size:28px;line-height:1}
.topbar img{height:40px;max-width:120px;width:auto;object-fit:contain;}
@media (max-width:480px){ .topbar img{height:28px;max-width:90px;} }

/* 카드 */
.chat-card{background:#fff;border-radius:24px;box-shadow:0 12px 40px rgba(0,0,0,.12);padding:16px 16px 8px;margin:8px 12px 20px}

/* 말풍선 */
.chat-bubble{display:block;clear:both;max-width:80%;padding:12px 16px;border-radius:16px;margin:12px 0;line-height:1.45;white-space:pre-wrap;word-break:break-word}
.user-bubble{background:#DCF8C6;float:right;text-align:right}
.assistant-bubble{background:#F1F0F0;float:left;text-align:left}

/* ===== 퀵버튼: 항상 3열 고정 ===== */
.quick-title{color:#fff;font-weight:700;margin:4px 0 8px 16px}
.chip-row { margin: 0 16px 10px 16px; }

/* 기본(모든 해상도) – st.columns 영역을 grid 3칸으로 강제 */
.chip-row [data-testid="stHorizontalBlock"]{
  display:grid !important;
  grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
  gap:10px !important;
  align-items:stretch !important;
}
.chip-row [data-testid="stHorizontalBlock"] > div,
.chip-row [data-testid="column"]{
  padding:0 !important;
  width:auto !important;
  flex:unset !important;
  max-width:none !important;
}

/* 640px 이하에서도 동일하게 3칸 유지(일부 브라우저용 보강) */
@media (max-width: 640px){
  .chip-row [data-testid="stHorizontalBlock"]{
    display:grid !important;
    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
    gap:10px !important;
  }
  .chip-row [data-testid="stHorizontalBlock"] > div,
  .chip-row [data-testid="column"]{
    padding:0 !important; flex:unset !important; width:auto !important; max-width:none !important;
  }
}

/* 버튼을 칩처럼 보이게 (pill, radius 100) */
.chip-btn .stButton>button{
  width:100%;
  height:40px;
  border-radius:100px !important;
  background:#fff !important;
  color:#1F55A4 !important;
  border:1px solid #7B2BFF !important;
  font-weight:800; font-size:12px;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
  box-shadow:0 2px 6px rgba(0,0,0,.08);
}
.chip-btn .stButton>button:hover,
.chip-btn .stButton>button:focus{ background:#fff !important; }

/* 스피너(말감이 생각 중…) 흰색 */
[data-testid="stSpinner"], [data-testid="stSpinner"] * {color:#FFFFFF !important;}
[data-testid="stSpinner"] svg circle{stroke:#FFFFFF !important;}
[data-testid="stSpinner"] svg path{stroke:#FFFFFF !important; fill:#FFFFFF !important;}

/* 입력창(네가 쓰던 스타일 유지) */
[data-testid="stChatInput"]{
  background:#F5F1FF!important;border-radius:999px!important;border:1px solid #E0CCFF!important;
  box-shadow:0 -2px 8px rgba(123,43,255,.15)!important;padding:6px 12px!important
}
[data-testid="stChatInput"]:focus-within{border:2px solid #7B2BFF!important;box-shadow:0 0 8px rgba(123,43,255,.35)!important}
[data-testid="stChatInput"] textarea,[data-testid="stChatInput"] input,[data-testid="stChatInput"] div[contenteditable="true"]{border:none!important;outline:none!important;box-shadow:none!important;background:transparent!important}
[data-testid="stChatInput"] button svg path{fill:#7B2BFF!important}
</style>
""", unsafe_allow_html=True)

# ----------------- 상단 바 -----------------
st.markdown(f'<div class="topbar">{logo_tag("logo.png")}<h1>말감 챗봇</h1></div>', unsafe_allow_html=True)

# ----------------- 카드 시작 -----------------
st.markdown('<div class="chat-card">', unsafe_allow_html=True)

# ----------------- 세션 -----------------
SYSTEM = """#지침: 너는 ui/ux 기획, 디자인, 리서처 업무를 도와주는 말감이야.
친근하게 답하고 마지막에 답변에 맞는 이모지 추가. 영어 질문도 한글로 답변."""
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

# ========= 1) 안내 말풍선 먼저 =========
if not st.session_state.welcome_shown:
    st.markdown(f'<div class="chat-bubble assistant-bubble">{WELCOME}</div>', unsafe_allow_html=True)
    st.session_state.welcome_shown = True

# ========= 2) 퀵버튼(3×3, 리로드 없음) =========
st.markdown('<div class="quick-title">아래 키워드로 물어볼 수도 있겠감</div>', unsafe_allow_html=True)

chips = [
  "📝AI 기획서 작성","🛠️툴 추천","💡아이디어 확장",
  "🔍AI 리서치","🎨피그마 사용법","📄노션 사용법",
  "🖱️프로토타입 팁","👥UX 리서치 설계","💬프롬프트 가이드"
]

for i in range(0, len(chips), 3):
    st.markdown('<div class="chip-row">', unsafe_allow_html=True)   # 3열 고정 래퍼
    cols = st.columns(3, gap="small")
    for c, label in zip(cols, chips[i:i+3]):
        with c:
            st.markdown('<div class="chip-btn">', unsafe_allow_html=True)
            if st.button(label, key=f"chip_{i}_{label}", use_container_width=True):
                send_and_stream(label)  # ✅ 리로드 없이 전송
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ========= 3) 대화 렌더 =========
for m in st.session_state.messages:
    if m["role"] == "system":
        continue
    cls = "user-bubble" if m["role"] == "user" else "assistant-bubble"
    st.markdown(f'<div class="{cls} chat-bubble">{m["content"]}</div>', unsafe_allow_html=True)

# ========= 4) 입력창 =========
if txt := st.chat_input("말감이가 기다리는 중!🥔"):
    send_and_stream(txt)

# ----------------- 카드 종료 -----------------
st.markdown('</div>', unsafe_allow_html=True)
