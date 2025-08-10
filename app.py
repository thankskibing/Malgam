from openai import OpenAI
import streamlit as st

# ----------------- 기본 설정 -----------------
st.set_page_config(page_title="말감 챗봇", page_icon="🥔", layout="centered")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ----------------- 스타일 -----------------
st.markdown("""
<style>
/* 상단 숨기기 + 배경 */
[data-testid="stHeader"]{display:none;}
.stApp{background:linear-gradient(180deg,#7B2BFF 0%,#8A39FF 35%,#A04DFF 100%)!important;}
.block-container{padding-top:0!important;}

.top-bar{display:flex;align-items:center;gap:12px;padding:20px 16px 8px;}
.top-bar h1{color:#fff;font-size:28px;margin:0;line-height:1}

.chat-card{background:#fff;border-radius:24px;box-shadow:0 12px 40px rgba(0,0,0,.12);padding:16px 16px 8px;margin:8px 12px 20px}

/* 말풍선 */
.chat-bubble{display:block;clear:both;max-width:80%;padding:12px 16px;border-radius:16px;margin:10px 0;line-height:1.4;white-space:pre-wrap;word-break:break-word}
.user-bubble{background:#DCF8C6;float:right;text-align:right}
.assistant-bubble{background:#F1F0F0;float:left;text-align:left}

/* ===== 퀵칩 (3 x 3) ===== */
.quick-title{font-size:15px;margin:4px 0 6px 2px;color:#fff;font-weight:700}
.chips-block{margin:0 10px 16px 10px;}           /* 칩 영역과 말풍선 간격 */

.quick-row{margin-bottom:10px;}                  /* 줄 간격 10px */
.quick-row [data-testid="column"]{padding:0 5px;}/* 열 간격 = 10px 효과 */
.quick-row [data-testid="column"]:first-child{padding-left:0;}
.quick-row [data-testid="column"]:last-child{padding-right:0;}

.quick-btn > button{
  width:100%;
  background:#fff !important;
  color:#1F55A4 !important;
  border:1px solid #7B2BFF !important;
  border-radius:100px !important;                /* 더 동그랗게 */
  padding:10px 0 !important;
  font-size:14px !important; font-weight:800 !important;
  box-shadow:0 2px 6px rgba(0,0,0,.08);
  text-shadow:none !important;
  transition:background-color .2s ease, transform .06s ease;
  cursor:pointer;
}
.quick-btn > button:hover{background:#F5F1FF !important;}
.quick-btn > button:active{transform:scale(.98);}

/* 입력창 */
[data-testid="stChatInput"]{background:#F5F1FF!important;border-radius:999px!important;border:1px solid #E0CCFF!important;box-shadow:0 -2px 8px rgba(123,43,255,.15)!important;padding:6px 12px!important}
[data-testid="stChatInput"]:focus-within{border:2px solid #7B2BFF!important;box-shadow:0 0 8px rgba(123,43,255,.35)!important}
[data-testid="stChatInput"] textarea,[data-testid="stChatInput"] input,[data-testid="stChatInput"] div[contenteditable="true"]{border:none!important;outline:none!important;box-shadow:none!important;background:transparent!important}
[data-testid="stChatInput"] button svg path{fill:#7B2BFF!important}
</style>
""", unsafe_allow_html=True)

# ----------------- 헤더 + 카드 -----------------
st.markdown('<div class="top-bar"><h1>말감 챗봇</h1></div>', unsafe_allow_html=True)
st.markdown('<div class="chat-card">', unsafe_allow_html=True)

# ----------------- 세션 -----------------
SYSTEM = """#지침: 너는 ui/ux 기획, 디자인, 리서처 업무를 도와주는 말감이야.
말끝은 '감'으로, 항상 친근/이모지 추가, 영어 질문도 한글로 답변."""
WELCOME = "안녕하세요! 저는 여러분을 도와줄 ‘말하는 감자 말감이’예요. 궁금한 점이나 고민이 있다면 자유롭게 물어보라감!😊"

if "messages" not in st.session_state:
    st.session_state.messages = [{"role":"system","content":SYSTEM}]
if "welcome_shown" not in st.session_state:
    st.session_state.welcome_shown = False

# ----------------- 모델 호출 (화면 출력은 루프에서만) -----------------
def send_and_stream(user_text: str):
    st.session_state.messages.append({"role":"user","content":user_text})
    with st.spinner("말감이 생각 중… 🥔💭"):
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=st.session_state.messages,
            stream=True,
        )
        assistant = ""
        for ch in stream:
            assistant += ch.choices[0].delta.content or ""
        st.session_state.messages.append({"role":"assistant","content":assistant})

# ----------------- 퀵칩 (3개씩 × 3줄) -----------------
st.markdown('<p class="quick-title">아래 키워드로 물어볼 수도 있겠감</p>', unsafe_allow_html=True)
st.markdown('<div class="chips-block">', unsafe_allow_html=True)

chips = [
    "AI 기획서 작성","툴 추천","아이디어 확장",
    "AI 리서치","피그마 사용법","노션 사용법",
    "프로토타입 팁","UX 리서치 설계","프롬프트 가이드"
]

def render_row(row_items, row_key: str):
    st.markdown('<div class="quick-row">', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, label in enumerate(row_items):
        with cols[i]:
            # 버튼 + 도움말(툴팁)
            btn = st.button(label, key=f"chip_{row_key}_{i}", help="클릭하면 바로 전송돼요")
            # 버튼에 CSS 적용할 래퍼(빈 div)
            st.markdown('<div class="quick-btn"></div>', unsafe_allow_html=True)
            if btn:
                send_and_stream(label)
    st.markdown('</div>', unsafe_allow_html=True)

render_row(chips[0:3], "r1")
render_row(chips[3:6], "r2")
render_row(chips[6:9], "r3")

st.markdown('</div>', unsafe_allow_html=True)

# ----------------- 환영 메시지 (칩 아래 1회) -----------------
if not st.session_state.welcome_shown:
    st.markdown(f'<div class="chat-bubble assistant-bubble">{WELCOME}</div>', unsafe_allow_html=True)
    st.session_state.welcome_shown = True

# ----------------- 대화 렌더(한 곳에서만) -----------------
for m in st.session_state.messages:
    if m["role"] == "system":
        continue
    cls = "user-bubble" if m["role"] == "user" else "assistant-bubble"
    st.markdown(f'<div class="{cls} chat-bubble">{m["content"]}</div>', unsafe_allow_html=True)

# ----------------- 입력창 -----------------
if txt := st.chat_input("말감이에게 궁금한걸 말해보세요!"):
    send_and_stream(txt)

st.markdown('</div>', unsafe_allow_html=True)
