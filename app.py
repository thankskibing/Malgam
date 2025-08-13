from openai import OpenAI
import streamlit as st
from pathlib import Path
import base64
from datetime import datetime, timezone, timedelta

# ----------------- 기본 -----------------
st.set_page_config(page_title="말감 챗봇", page_icon="🥔", layout="centered")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

KST = timezone(timedelta(hours=9))

# ----------------- 인라인 이미지 태그 -----------------
def inline_img_tag(path, alt="img", style=""):
    p = Path(path)
    if not p.exists():
        for c in [Path("static")/path, Path("assets")/path, Path("app/static")/path]:
            if c.exists(): p = c; break
    if not p.exists():
        return ""
    data = base64.b64encode(p.read_bytes()).decode()
    ext = (p.suffix[1:] or "png")
    return f'<img src="data:image/{ext};base64,{data}" alt="{alt}" style="{style}"/>'

def logo_tag(path="logo.png"):
    return inline_img_tag(path, "logo", "height:40px;max-width:120px;width:auto;object-fit:contain;")

def avatar_tag(path, size=36, alt="avatar"):
    return inline_img_tag(path, alt, f"width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;")

# ----------------- 시간 포맷 -----------------
def ts_now_utc():
    return datetime.now(timezone.utc).isoformat()

def ts_hhmm_kst(ts_iso):
    try:
        dt = datetime.fromisoformat(ts_iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        kst = dt.astimezone(KST)
        return kst.strftime("%I:%M %p").lstrip("0")  # ex) 9:59 PM
    except Exception:
        return ""

# ----------------- 스타일 -----------------
st.markdown("""
<style>
/* 헤더 숨기기 + 배경 */
[data-testid="stHeader"]{display:none;}
.stApp{background:linear-gradient(180deg,#7B2BFF 0%,#8A39FF 35%,#A04DFF 100%)!important;}
.block-container{padding-top:0!important}

/* 상단 바 */
.topbar{
    display:flex;
    align-items:center;
    gap:12px;
    padding:12px 16px 4px; /* 하단 여백 줄임 */
}
.topbar h1{color:#fff;margin:0;font-size:28px;line-height:1}
@media (max-width:480px){ .topbar img{height:28px;max-width:90px;} }

/* 카드 */
.chat-card{
    background:transparent;
    border-radius:24px;
    padding:8px 12px;
    margin:0px 12px 20px; /* 상단 간격 0px */
}

/* 행 레이아웃 */
.chat-row{display:flex;gap:10px;align-items:flex-start;margin:12px 0}
.chat-row.left{flex-direction:row}
.chat-row.right{flex-direction:row-reverse}
.chat-wrap{max-width:78%}

/* 이름(상단) — 흰색, 크게 */
.chat-meta{font-size:16px;color:#FFFFFF;margin:0 4px 6px 4px;font-weight:800}

/* 말풍선 */
.chat-bubble{display:block;max-width:100%;padding:14px 18px;border-radius:20px;line-height:1.55;white-space:pre-wrap;word-break:break-word}
.user-bubble{background:#DCF8C6;}
.assistant-bubble{background:#F1F0F0;}

/* 말풍선 하단 시간 — 항상 오른쪽 정렬 */
.chat-footer{font-size:12px;color:#EDE7FF;margin:6px 8px 0 8px;text-align:right}

/* 퀵칩 */
.quick-title{color:#fff;font-weight:800;margin:16px 0 10px 16px;font-size:20px}
.stButton > button {
  background:#fff !important; color:#1F55A4 !important; border:1px solid #7B2BFF !important;
  border-radius:100px !important; padding:8px 10px !important; font-weight:800 !important; 
  font-size:12px !important; white-space:nowrap !important; overflow:hidden !important;
  text-overflow:ellipsis !important; box-shadow:0 2px 6px rgba(0,0,0,.08) !important;
  transition:background-color .2s, transform .06s !important; cursor:pointer !important;
  width:100% !important; min-height:40px !important;
}
.stButton > button:hover{ background:#F5F1FF !important; }
.stButton > button:active{ transform:scale(.98) !important; }

/* 스피너/입력창 */
[data-testid="stSpinner"], [data-testid="stSpinner"] * {color:#FFFFFF !important;}
[data-testid="stSpinner"] svg circle{stroke:#FFFFFF !important;}
[data-testid="stSpinner"] svg path{stroke:#FFFFFF !important; fill:#FFFFFF !important;}
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

# ----------------- API 호출/스트리밍 -----------------
def send_and_stream(user_text: str):
    st.session_state.messages.append(
        {"role":"user","content":user_text,"name":"나","ts":ts_now_utc()}
    )
    api_msgs = [{"role":m["role"],"content":m["content"]}
                for m in st.session_state.messages
                if m["role"] in ("system","user","assistant")]
    with st.spinner("🥔💭말감이 생각 중…"):
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=api_msgs,
            stream=True,
        )
        assistant = ""
        for ch in stream:
            assistant += (ch.choices[0].delta.content or "")
        st.session_state.messages.append(
            {"role":"assistant","content":assistant,"name":"말감","ts":ts_now_utc()}
        )

# ----------------- 환영 메시지 -----------------
if not st.session_state.welcome_shown:
    st.session_state.messages.append(
        {"role":"assistant","content":WELCOME,"name":"말감","ts":ts_now_utc()}
    )
    st.session_state.welcome_shown = True

# ----------------- 대화 렌더 -----------------
ASSISTANT_AVATAR = "user.png"
for m in st.session_state.messages:
    if m["role"] == "system":
        continue
    is_user = (m["role"] == "user")
    side = "right" if is_user else "left"
    bubble_cls = "user-bubble" if is_user else "assistant-bubble"
    name = m.get("name", "나" if is_user else "말감")
    time_txt = ts_hhmm_kst(m.get("ts",""))
    ava_html = avatar_tag(ASSISTANT_AVATAR, size=36, alt="말감") if not is_user else '<div style="width:36px;height:36px"></div>'
    st.markdown(
        f'''
<div class="chat-row {side}">
  <div class="avatar">{ava_html}</div>
  <div class="chat-wrap">
    <div class="chat-meta">{name}</div>
    <div class="{bubble_cls} chat-bubble">{m["content"]}</div>
    <div class="chat-footer">{time_txt}</div>
  </div>
</div>
''', unsafe_allow_html=True)

# ----------------- 퀵칩 -----------------
st.markdown('<div class="quick-title">아래 키워드를 선택해 물어보라감</div>', unsafe_allow_html=True)
chip_data = ["👥UX 리서치 설계","📝AI 기획서 작성","🛠️툴 추천","💬프롬프트 가이드","🎨피그마 사용법","📄노션 사용법"]
col1,col2,col3 = st.columns(3)
with col1:
    if st.button(chip_data[0], key="chip_0", use_container_width=True):
        send_and_stream(chip_data[0]); st.rerun()
with col2:
    if st.button(chip_data[1], key="chip_1", use_container_width=True):
        send_and_stream(chip_data[1]); st.rerun()
with col3:
    if st.button(chip_data[2], key="chip_2", use_container_width=True):
        send_and_stream(chip_data[2]); st.rerun()
col4,col5,col6 = st.columns(3)
with col4:
    if st.button(chip_data[3], key="chip_3", use_container_width=True):
        send_and_stream(chip_data[3]); st.rerun()
with col5:
    if st.button(chip_data[4], key="chip_4", use_container_width=True):
        send_and_stream(chip_data[4]); st.rerun()
with col6:
    if st.button(chip_data[5], key="chip_5", use_container_width=True):
        send_and_stream(chip_data[5]); st.rerun()

# ----------------- 입력창 -----------------
if txt := st.chat_input("말감이가 질문 기다리는 중!🥔"):
    send_and_stream(txt); st.rerun()

# ----------------- 카드 종료 -----------------
st.markdown('</div>', unsafe_allow_html=True)
