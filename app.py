from openai import OpenAI
import streamlit as st
from urllib.parse import quote, unquote
from pathlib import Path
import base64

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
  --chat-input-h: 64px;   /* 데스크톱 입력창 높이 추정 */
  --chips-h: 120px;       /* 퀵칩 영역 높이(타이틀+칩 2줄 가정) */
}

/* 헤더 숨기기 + 배경 */
[data-testid="stHeader"]{display:none;}
.stApp{background:linear-gradient(180deg,#7B2BFF 0%,#8A39FF 35%,#A04DFF 100%)!important;}
/* 하단 고정 UI(칩+입력창)가 본문을 가리지 않도록 패딩 확보 */
.block-container{
  padding-top:0!important;
  padding-bottom: calc(var(--chips-h) + var(--chat-input-h) + 16px) !important;
}

/* 상단바 */
.topbar{display:flex;align-items:center;gap:12px;padding:20px 16px 8px}
.topbar h1{color:#fff;margin:0;font-size:28px;line-height:1}
.topbar img{height:40px;max-width:120px;width:auto;object-fit:contain;}
@media (max-width:480px){ .topbar img{height:28px;max-width:90px;} }

/* 카드 */
.chat-card{
  background:#fff;border-radius:24px;box-shadow:0 12px 40px rgba(0,0,0,.12);
  padding:16px 16px 8px;margin:8px 12px 24px;
}

/* 말풍선 */
.chat-bubble{display:block;clear:both;max-width:80%;padding:12px 16px;border-radius:16px;margin:12px 0;line-height:1.45;white-space:pre-wrap;word-break:break-word}
.user-bubble{background:#DCF8C6;float:right;text-align:right}
.assistant-bubble{background:#F1F0F0;float:left;text-align:left}

/* 스피너(흰색) */
[data-testid="stSpinner"], [data-testid="stSpinner"] * {color:#FFFFFF !important;}
[data-testid="stSpinner"] svg circle{stroke:#FFFFFF !important;}
[data-testid="stSpinner"] svg path{stroke:#FFFFFF !important; fill:#FFFFFF !important;}

/* ===== 입력창: 화면 하단 고정, 최상단 z-index 보장 ===== */
[data-testid="stChatInput"]{
  position: fixed; left: 0; right: 0; bottom: 0;
  z-index: 2147483647; /* 최우선 */
  background:#F5F1FF!important;border-radius:999px!important;border:1px solid #E0CCFF!important;
  box-shadow:0 -2px 8px rgba(123,43,255,.15)!important;padding:6px 12px!important
}
[data-testid="stChatInput"]:focus-within{border:2px solid #7B2BFF!important;box-shadow:0 0 8px rgba(123,43,255,.35)!important}
[data-testid="stChatInput"] textarea,[data-testid="stChatInput"] input,[data-testid="stChatInput"] div[contenteditable="true"]{border:none!important;outline:none!important;box-shadow:none!important;background:transparent!important}
[data-testid="stChatInput"] button svg path{fill:#7B2BFF!important}

/* ===== 퀵칩: 입력창 바로 위에 고정 (입력창보다 낮은 z-index) ===== */
.chips-fixed{
  position: fixed;
  left: 0; right: 0;
  bottom: var(--chat-input-h);
  z-index: 2147483000; /* 입력창보다 낮게 */
  background: linear-gradient(180deg,#7B2BFF 0%,#8A39FF 60%,#A04DFF 100%);
  padding: 12px 16px 14px;
  box-shadow: 0 -4px 12px rgba(0,0,0,.15);
}
.chips-fixed .quick-title{color:#fff;font-weight:700;margin:0 0 8px 4px}
.chips-fixed .chip-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;}
.chips-fixed .chip{display:flex}
.chips-fixed .chip a{
  flex:1;display:inline-flex;align-items:center;justify-content:center;
  text-decoration:none;background:#fff;color:#1F55A4;border:1px solid #7B2BFF;
  border-radius:100px;padding:8px 12px;font-weight:800;font-size:12px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
  box-shadow:0 2px 6px rgba(0,0,0,.08);transition:background-color .2s, transform .06s;
}
.chips-fixed .chip a:hover{background:#F5F1FF}
.chips-fixed .chip a:active{transform:scale(.98)}

/* 모바일 높이 보정 */
@media (max-width: 480px){
  :root{ --chat-input-h: 76px; }
}
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

# ================= 전송 함수 (완성 후 한 번에 표시: 타자 효과 OFF) =================
def send_and_stream(user_text: str):
    # 1) 유저 메시지 저장
    st.session_state.messages.append({"role":"user","content":user_text})

    # 2) 생성 중에는 스피너만 보이게 하고, 중간 출력은 하지 않음
    with st.spinner("🥔💭말감이 생각 중…"):
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.messages,
            stream=True,
        )
        chunks = []
        for ch in stream:
            token = ch.choices[0].delta.content
            if token:
                chunks.append(token)

    # 3) 완성된 후에만 한 번에 추가/표시
    assistant = "".join(chunks)
    st.session_state.messages.append({"role":"assistant","content":assistant})

    # 4) 새 상태로 즉시 재렌더
    st.rerun()

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

# ========= (B) 퀵칩 URL 파라미터 → 안전한 2-스텝 처리 =========
qp = st.query_params
raw = qp.get("chip", None)

if raw:
    picked_raw = raw[0] if isinstance(raw, list) else raw
    picked = unquote(picked_raw)

    # 1) URL 파라미터 먼저 제거(중복 처리/깜빡임 방지)
    try:
        if "chip" in st.query_params:
            del st.query_params["chip"]
    except Exception:
        try:
            st.query_params.clear()
        except Exception:
            pass

    # 2) 다음 렌더에서 전송하도록 세션에 저장 후 재실행
    st.session_state["_pending_chip"] = picked
    st.rerun()

# 다음 렌더에서만 실제 전송 실행 (URL 파라미터 없음 → 안정)
if st.session_state.get("_pending_chip"):
    picked = st.session_state.pop("_pending_chip")
    send_and_stream(picked)  # 내부에서 완성 후 한 번에 표시 + rerun

# ================= 대화 렌더 (입력/칩 처리 뒤) =================
for m in st.session_state.messages:
    if m["role"] == "system":
        continue
    cls = "user-bubble" if m["role"] == "user" else "assistant-bubble"
    st.markdown(f'<div class="{cls} chat-bubble">{m["content"]}</div>', unsafe_allow_html=True)

# ================= 카드 종료 =================
st.markdown('</div>', unsafe_allow_html=True)

# ================= 퀵칩(입력창 위 고정) =================
chips = [
  "👥UX 리서치 설계","📝AI 기획서 작성","🛠️툴 추천",
  "💬프롬프트 가이드","🎨피그마 사용법","📄노션 사용법"
]
html = ['<div class="chips-fixed"><div class="quick-title">아래 키워드로 물어보라감</div><div class="chip-grid">']
for label in chips:
    html.append(f'<div class="chip"><a href="?chip={quote(label)}" target="_self" title="클릭하면 바로 전송돼요">{label}</a></div>')
html.append('</div></div>')
st.markdown("".join(html), unsafe_allow_html=True)
