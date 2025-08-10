from openai import OpenAI
import streamlit as st

# ----------------- 기본 설정 -----------------
st.set_page_config(page_title="말감 챗봇", page_icon="🥔", layout="centered")
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ----------------- 스타일 -----------------
st.markdown("""
<style>
/* 상단 기본 헤더/경계선 완전 제거 */
[data-testid="stHeader"] { display: none; }

/* 앱 전체 배경 (보라 그라데이션) */
.stApp { background: linear-gradient(180deg,#7B2BFF 0%,#8A39FF 35%,#A04DFF 100%) !important; }

/* 메인 컨테이너 상단 여백 최소화 */
.block-container { padding-top: 0 !important; }

/* 상단 커스텀 바 */
.top-bar { display:flex; align-items:center; gap:12px; padding:20px 16px 8px; }
.top-bar img { height:48px; }
.top-bar h1 { color:#fff; font-size:28px; margin:0; line-height:1; }

/* 카드 */
.chat-card { background:#fff; border-radius:24px; box-shadow:0 12px 40px rgba(0,0,0,.12);
             padding:16px 16px 8px; margin:8px 12px 20px; }

/* 말풍선 */
.chat-bubble{display:block;clear:both;max-width:80%;padding:12px 16px;border-radius:16px;margin:8px 0;
             line-height:1.4;white-space:pre-wrap;word-break:break-word;}
.user-bubble{background:#DCF8C6;float:right;text-align:right;}
.assistant-bubble{background:#F1F0F0;float:left;text-align:left;}

/* ===== 빠른 답변(칩) - 한 줄 고정 5등분 ===== */
.quick-title{ font-size:15px; margin:4px 0 10px 2px; color:#fff; font-weight:700; }

/* 한 줄, 줄바꿈 없음, 칩 사이 gap 10px */
.quick-row{
  display:flex; flex-wrap:nowrap; gap:10px; padding:4px 16px 14px;
}
/* 각 st.button 컨테이너를 동일 폭으로 */
.quick-row .stButton{
  flex:1 1 0;            /* 균등 분배 */
  min-width:0;           /* 넘침 방지 */
  margin:0;
}
/* 칩 버튼 스타일 (폭 100%) */
.quick-row .stButton > button{
  width:100%;
  background:#FFFFFF !important;
  color:#1F55A4 !important;
  border:1px solid #7B2BFF !important;
  border-radius:999px !important;
  padding:10px 0 !important;                 /* 좌우 여백 최소화로 텍스트 공간 확보 */
  font-size:clamp(12px, 2.6vw, 14px) !important;  /* 화면폭에 맞춰 살짝 축소 */
  font-weight:800 !important;
  box-shadow:0 2px 6px rgba(0,0,0,.08);
  text-shadow:none !important;
  transition: background-color .2s ease, transform .06s ease;
  cursor:pointer;
}
.quick-row .stButton > button:hover{
  background:#F5F1FF !important;
  border-color:#7B2BFF !important;
}
.quick-row .stButton > button:active{ transform:scale(.98); }

/* 보라 라운드 툴팁 */
[data-testid="stTooltip"] div, div[role="tooltip"], [data-baseweb="tooltip"]{
  background:#7B2BFF !important; color:#fff !important; border-radius:100px !important;
  padding:6px 10px !important; box-shadow:0 6px 16px rgba(123,43,255,.25) !important; border:0 !important;
}

/* ===== 입력창 스타일 ===== */
[data-testid="stChatInput"] {
  background-color:#F5F1FF !important;
  border-radius:999px !important;
  border:1px solid #E0CCFF !important;
  box-shadow:0 -2px 8px rgba(123,43,255,.15) !important;
  padding:6px 12px !important;
  transition:border .2s ease, box-shadow .2s ease;
}
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] input,
[data-testid="stChatInput"] div[contenteditable="true"]{
  border:none !important; outline:none !important; box-shadow:none !important; background:transparent !important;
}
[data-testid="stChatInput"]:focus-within {
  border:2px solid #7B2BFF !important;
  box-shadow:0 0 8px rgba(123,43,255,.35) !important;
}
[data-testid="stChatInput"] button svg path { fill:#7B2BFF !important; }
</style>
""", unsafe_allow_html=True)

# ----------------- 상단 바 -----------------
left, right = st.columns([1, 10])
with left:
    st.image("logo.png")
with right:
    st.markdown('<div class="top-bar"><h1>말감 챗봇</h1></div>', unsafe_allow_html=True)

# ----------------- 카드 시작 -----------------
st.markdown('<div class="chat-card">', unsafe_allow_html=True)

# ----------------- 시스템 / 세션 초기화 -----------------
SYSTEM_MSG = '''
#지침: 너는 ui/ux 기획, 디자인, 리서처 업무를 도와주는 이름은 말감이야.
너는 피그마나 디자인, ai 관련한 질문을 받아주고 고민 상담도 들어줘
너는 항상 감으로 문장을 끝내주고 항상 친근하게 대답해줘.
영어로 질문을 받아도 무조건 한글로 답변해줘.
한글이 아닌 답변일 때는 다시 생각해서 꼭 한글로 만들어줘
모든 답변 끝에 답변에 맞는 이모티콘도 추가해줘
'''
WELCOME = "안녕하세요! 저는 여러분을 도와줄 ‘말하는 감자 말감이’예요. 궁금한 점이나 고민이 있다면 자유롭게 물어보라감!😊"

if "messages" not in st.session_state:
    st.session_state.messages = [{"role":"system","content":SYSTEM_MSG}]
if "welcome_shown" not in st.session_state:
    st.session_state.welcome_shown = False

# ----------------- 공통 전송 함수 -----------------
def send_and_stream(user_text: str):
    st.session_state.messages.append({"role":"user","content":user_text})
    st.markdown(f'<div class="chat-bubble user-bubble">{user_text}</div>', unsafe_allow_html=True)

    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=st.session_state.messages,
        stream=True,
    )
    assistant_text = ""
    for chunk in stream:
        assistant_text += chunk.choices[0].delta.content or ""
    st.markdown(f'<div class="chat-bubble assistant-bubble">{assistant_text}</div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role":"assistant","content":assistant_text})

# ----------------- 빠른 답변(한 줄 5개, 클릭 즉시 전송) -----------------
st.markdown('<p class="quick-title">아래 키워드로 물어볼 수도 있겠감</p>', unsafe_allow_html=True)

quick_items = ["AI 기획서 작성", "툴 추천", "아이디어 확장", "AI 리서치", "피그마 사용법"]  # 정확히 5개

st.markdown('<div class="quick-row">', unsafe_allow_html=True)
for i, label in enumerate(quick_items):
    if st.button(label, key=f"quick_{i}", help="클릭하면 바로 전송돼요"):
        send_and_stream(label)  # ✅ 즉시 전송
st.markdown('</div>', unsafe_allow_html=True)

# ----------------- 인사 말풍선 (버튼 아래 1회) -----------------
if not st.session_state.welcome_shown:
    st.markdown(f'<div class="chat-bubble assistant-bubble">{WELCOME}</div>', unsafe_allow_html=True)
    st.session_state.welcome_shown = True

# ----------------- 기존 메시지 렌더 -----------------
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    klass = "user-bubble" if msg["role"] == "user" else "assistant-bubble"
    st.markdown(f'<div class="chat-bubble {klass}">{msg["content"]}</div>', unsafe_allow_html=True)

# ----------------- 입력창 -----------------
if prompt := st.chat_input("말감이에게 궁금한걸 말해보세요!"):
    send_and_stream(prompt)

# ----------------- 카드 종료 -----------------
st.markdown('</div>', unsafe_allow_html=True)
