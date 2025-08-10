from openai import OpenAI
import streamlit as st
from urllib.parse import quote, unquote

st.set_page_config(page_title="말감 챗봇", page_icon="🥔", layout="centered")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ---------- STYLE ----------
st.markdown("""
<style>
[data-testid="stHeader"]{display:none;}
.stApp{background:linear-gradient(180deg,#7B2BFF 0%,#8A39FF 35%,#A04DFF 100%)!important;}
.block-container{padding-top:0!important;}

.top-bar{display:flex;align-items:center;gap:12px;padding:20px 16px 8px;}
.top-bar h1{color:#fff;font-size:28px;margin:0;line-height:1}
.chat-card{background:#fff;border-radius:24px;box-shadow:0 12px 40px rgba(0,0,0,.12);padding:16px 16px 8px;margin:8px 12px 20px}

.quick-title{font-size:15px;margin:4px 0 6px 2px;color:#fff;font-weight:700}

/* === 칩 그리드 (정확히 gap:10px) === */
.chip-grid{display:grid;gap:10px;padding:0 16px;margin-bottom:8px}
.grid-5{grid-template-columns:repeat(5,minmax(0,1fr));}
.grid-4{grid-template-columns:repeat(4,minmax(0,1fr));}
.chip{display:flex}
.chip > a{
  flex:1 1 auto; display:inline-flex; align-items:center; justify-content:center;
  text-decoration:none;
  background:#fff; color:#1F55A4; border:1px solid #7B2BFF;
  border-radius:100px; padding:10px 12px; font-weight:800; font-size:14px;
  box-shadow:0 2px 6px rgba(0,0,0,.08); transition:background-color .2s, transform .06s;
}
.chip > a:hover{background:#F5F1FF;}
.chip > a:active{transform:scale(.98);}

/* 말풍선 */
.chat-bubble{display:block;clear:both;max-width:80%;padding:12px 16px;border-radius:16px;margin:8px 0;line-height:1.4;white-space:pre-wrap;word-break:break-word}
.user-bubble{background:#DCF8C6;float:right;text-align:right}
.assistant-bubble{background:#F1F0F0;float:left;text-align:left}

/* 입력창 */
[data-testid="stChatInput"]{background:#F5F1FF!important;border-radius:999px!important;border:1px solid #E0CCFF!important;box-shadow:0 -2px 8px rgba(123,43,255,.15)!important;padding:6px 12px!important}
[data-testid="stChatInput"]:focus-within{border:2px solid #7B2BFF!important;box-shadow:0 0 8px rgba(123,43,255,.35)!important}
[data-testid="stChatInput"] textarea,[data-testid="stChatInput"] input,[data-testid="stChatInput"] div[contenteditable="true"]{border:none!important;outline:none!important;box-shadow:none!important;background:transparent!important}
[data-testid="stChatInput"] button svg path{fill:#7B2BFF!important}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown('<div class="top-bar"><h1>말감 챗봇</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="chat-card">', unsafe_allow_html=True)

# ---------- SYSTEM / STATE ----------
SYSTEM = """#지침: 너는 ui/ux 기획, 디자인, 리서처 업무를 도와주는 이름은 말감이야.
영어로 질문을 받아도 무조건 한글로 답변하고, 말 끝을 '감'으로 마무리, 이모지 추가."""
WELCOME = "안녕하세요! 저는 여러분을 도와줄 ‘말하는 감자 말감이’예요. 궁금한 점이나 고민이 있다면 자유롭게 물어보라감!😊"

if "messages" not in st.session_state:
    st.session_state.messages = [{"role":"system","content":SYSTEM}]
if "welcome_shown" not in st.session_state:
    st.session_state.welcome_shown = False

def send_and_stream(user_text:str):
    st.session_state.messages.append({"role":"user","content":user_text})
    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=st.session_state.messages,
        stream=True,
    )
    assistant = ""
    for ch in stream:
        assistant += ch.choices[0].delta.content or ""
    st.session_state.messages.append({"role":"assistant","content":assistant})

# ---------- QUICK CHIPS (5 + 4, gap=10px 정확히) ----------
st.markdown('<p class="quick-title">아래 키워드로 물어볼 수도 있겠감</p>', unsafe_allow_html=True)

items = [
    "AI 기획서 작성", "툴 추천", "아이디어 확장",
    "AI 리서치", "피그마 사용법",
    "노션 사용법", "프로토타입 팁", "UX 리서치 설계", "프롬프트 가이드"
]

# 1줄(5)
html = ['<div class="chip-grid grid-5">']
for label in items[:5]:
    html += [f'<div class="chip"><a href="?chip={quote(label)}" target="_self" title="클릭하면 바로 전송돼요">{label}</a></div>']
html += ['</div>']
# 2줄(4)
html += ['<div class="chip-grid grid-4">']
for label in items[5:]:
    html += [f'<div class="chip"><a href="?chip={quote(label)}" target="_self" title="클릭하면 바로 전송돼요">{label}</a></div>']
html += ['</div>']
st.markdown("".join(html), unsafe_allow_html=True)

# ---------- WELCOME (chips 아래 1회) ----------
if not st.session_state.welcome_shown:
    st.markdown(f'<div class="chat-bubble assistant-bubble">{WELCOME}</div>', unsafe_allow_html=True)
    st.session_state.welcome_shown = True

# ---------- HANDLE CHIP CLICK (즉시 전송, URL 정리) ----------
qp = st.query_params
if "chip" in qp:
    picked = unquote(qp["chip"])
    send_and_stream(picked)
    del st.query_params["chip"]
    st.rerun()

# ---------- RENDER DIALOG ----------
for m in st.session_state.messages:
    if m["role"] == "system": 
        continue
    cls = "user-bubble" if m["role"]=="user" else "assistant-bubble"
    st.markdown(f'<div class="{cls} chat-bubble">{m["content"]}</div>', unsafe_allow_html=True)

# ---------- INPUT ----------
if txt := st.chat_input("말감이에게 궁금한걸 말해보세요!"):
    send_and_stream(txt)
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
