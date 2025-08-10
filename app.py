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

/* ===== 퀵칩: 전 해상도 3열 × 3줄 고정 ===== */
.quick-title{color:#fff;font-weight:700;margin:4px 0 8px 16px}
.chips-wrap{margin:0 16px 18px 16px}
.chip-grid{
  display:grid !important;
  grid-template-columns:repeat(3,minmax(0,1fr)) !important;  /* 항상 3열 유지 */
  gap:10px !important;
  width:100% !important;
}
.chip{
  display:flex !important;
}
.chip-btn{
  flex:1 1 auto !important; 
  display:inline-flex !important; 
  align-items:center !important; 
  justify-content:center !important;
  background:#fff !important; 
  color:#1F55A4 !important; 
  border:1px solid #7B2BFF !important;
  border-radius:100px !important; 
  padding:8px 10px !important;            
  font-weight:800 !important; 
  font-size:12px !important;                  
  white-space:nowrap !important; 
  overflow:hidden !important; 
  text-overflow:ellipsis !important;  
  box-shadow:0 2px 6px rgba(0,0,0,.08) !important; 
  transition:background-color .2s, transform .06s !important;
  cursor:pointer !important;
  width: 100% !important;
}
.chip-btn:hover{
  background:#F5F1FF !important;
}
.chip-btn:active{
  transform:scale(.98) !important;
}

/* 히든 input 숨기기 */
input[data-testid*="chip_receiver"], 
div[data-testid*="chip_receiver"] {
  display: none !important;
  visibility: hidden !important;
  height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
}

/* ===== 스피너(말감이 생각 중…) 완전 흰색 ===== */
[data-testid="stSpinner"], [data-testid="stSpinner"] * {color:#FFFFFF !important;}
[data-testid="stSpinner"] svg circle{stroke:#FFFFFF !important;}
[data-testid="stSpinner"] svg path{stroke:#FFFFFF !important; fill:#FFFFFF !important;}

/* 입력창 */
[data-testid="stChatInput"]{background:#F5F1FF!important;border-radius:999px!important;border:1px solid #E0CCFF!important;box-shadow:0 -2px 8px rgba(123,43,255,.15)!important;padding:6px 12px!important}
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
WELCOME = "안녕하세요! 저는 여러분을 도와줄 '말하는 감자 말감이'예요. 궁금한 점이나 고민이 있다면 자유롭게 물어보라감!😊"

if "messages" not in st.session_state:
    st.session_state.messages = [{"role":"system","content":SYSTEM}]
if "welcome_shown" not in st.session_state:
    st.session_state.welcome_shown = False
if "selected_chip" not in st.session_state:
    st.session_state.selected_chip = None

# ----------------- 응답 함수 (흰색 스피너, 출력은 루프에서만) -----------------
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

# ----------------- 퀵칩 (3 × 3) - CSS Grid로 강제 3열 유지 -----------------
st.markdown('<div class="quick-title">아래 키워드로 물어볼 수도 있겠감</div>', unsafe_allow_html=True)

chips = [
    "📝AI 기획서 작성","🛠️툴 추천","💡아이디어 확장",
    "🔍AI 리서치","🎨피그마 사용법","📄노션 사용법",
    "🖱️프로토타입 팁","👥UX 리서치 설계","💬프롬프트 가이드"
]

# ----------------- 퀵칩 (3 × 3) - 간단한 HTML 버튼 -----------------
st.markdown('<div class="quick-title">아래 키워드로 물어보겠감</div>', unsafe_allow_html=True)

chips = [
    "📝AI 기획서 작성","🛠️툴 추천","💡아이디어 확장",
    "🔍AI 리서치","🎨피그마 사용법","📄노션 사용법",
    "🖱️프로토타입 팁","👥UX 리서치 설계","💬프롬프트 가이드"
]

# 간단한 HTML 버튼으로 구현
chip_html = """
<div class="chips-wrap">
    <div class="chip-grid">"""

for i, chip in enumerate(chips):
    chip_html += f"""
        <div class="chip">
            <button class="chip-btn" onclick="document.getElementById('chip_value').value='{chip}'; document.getElementById('chip_value').dispatchEvent(new Event('input'));">
                {chip}
            </button>
        </div>"""

chip_html += """
    </div>
</div>
<input type="hidden" id="chip_value" />
"""

st.markdown(chip_html, unsafe_allow_html=True)

# 히든 값 받기 - 더 간단한 방법
if "chip_clicked" not in st.session_state:
    st.session_state.chip_clicked = ""

# JavaScript로 전달된 값 받기
chip_value = st.text_input("", key="chip_receiver", label_visibility="collapsed", placeholder="")

if chip_value and chip_value != st.session_state.chip_clicked:
    st.session_state.selected_chip = chip_value
    st.session_state.chip_clicked = chip_value
    # 입력창 초기화
    st.session_state.chip_receiver = ""
    st.rerun()

# 선택된 칩 처리
if st.session_state.selected_chip:
    send_and_stream(st.session_state.selected_chip)
    st.session_state.selected_chip = None  # 처리 후 초기화

# ----------------- 환영 메시지 (칩 아래 1회) -----------------
if not st.session_state.welcome_shown:
    st.markdown(f'<div class="chat-bubble assistant-bubble">{WELCOME}</div>', unsafe_allow_html=True)
    st.session_state.welcome_shown = True

# ----------------- 대화 렌더 -----------------
for m in st.session_state.messages:
    if m["role"] == "system":
        continue
    cls = "user-bubble" if m["role"] == "user" else "assistant-bubble"
    st.markdown(f'<div class="{cls} chat-bubble">{m["content"]}</div>', unsafe_allow_html=True)

# ----------------- 입력창 -----------------
if txt := st.chat_input("말감이가 질문 기다리는 중!🥔"):
    send_and_stream(txt)

# ----------------- 카드 종료 -----------------
st.markdown('</div>', unsafe_allow_html=True)
