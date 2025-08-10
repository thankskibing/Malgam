from openai import OpenAI
import streamlit as st
from urllib.parse import quote, unquote

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

/* -------- 칩 캐러셀(페이지 넘김) -------- */
.quick-title{ font-size:15px; margin:4px 0 10px 2px; color:#fff; font-weight:700; }

.carousel { display:flex; align-items:center; gap:10px; padding:4px 16px 14px; }

/* 좌/우 화살표 (보조 버튼) */
.arrow .stButton > button{
  background:#fff !important; color:#7B2BFF !important;
  border:1px solid #E0CCFF !important; border-radius:999px !important;
  padding:6px 10px !important; font-weight:800 !important;
  box-shadow:0 2px 6px rgba(0,0,0,.06);
}
.arrow .stButton > button:hover{ background:#F5F1FF !important; }

/* 칩 래퍼: 한 줄에서 여러 개(페이지 내) */
.chips { display:flex; gap:10px; flex-wrap:nowrap; overflow:hidden; }

/* 칩 버튼(흰 배경 + 보라 테두리/글씨) */
.chip-btn{
  display:inline-flex; align-items:center; gap:6px; text-decoration:none;
  background:#FFFFFF; color:#1F55A4;                    /* 글씨는 약간 딥블루톤 */
  border:1px solid #7B2BFF; border-radius:999px;
  padding:8px 14px; font-size:14px; font-weight:800;
  box-shadow:0 2px 6px rgba(0,0,0,.08);
  transition:background-color .2s ease, transform .06s ease;
}
.chip-btn:hover{ background:#F5F1FF; border-color:#7B2BFF; }
.chip-btn:active{ transform:scale(.98); }

/* ===== 입력창 스타일 ===== */
[data-testid="stChatInput"] {
  background-color:#F5F1FF !important;
  border-radius:999px !important;
  border:1px solid #E0CCFF !important;
  box-shadow:0 -2px 8px rgba(123,43,255,.15) !important;
  padding:6px 12px !important;
  transition:border .2s ease, box-shadow .2s ease;
}
/* 내부 텍스트 입력요소의 기본 테두리/아웃라인 제거(빨간 테두리 제거) */
[data-testid="stChatInput"] textarea,
[data-testid="stChatInput"] input,
[data-testid="stChatInput"] div[contenteditable="true"]{
  border:none !important; outline:none !important; box-shadow:none !important; background:transparent !important;
}
/* 포커스 강조 */
[data-testid="stChatInput"]:focus-within {
  border:2px solid #7B2BFF !important;
  box-shadow:0 0 8px rgba(123,43,255,.35) !important;
}
/* 아이콘 보라 */
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

# ----------------- 칩 데이터 & 페이지 상태 -----------------
quick_items = [
    "AI 기획서 작성", "툴 추천", "아이디어 확장",
    "AI 리서치", "피그마 사용법", "노션 사용법",
    "프로토타입 팁", "UX 리서치 설계", "프롬프트 가이드"
]
VIEW_COUNT = 4  # 한 페이지 표시 개수 (모바일 3으로 조절 가능)
total_pages = max(1, (len(quick_items) + VIEW_COUNT - 1) // VIEW_COUNT)
if "chip_page" not in st.session_state:
    st.session_state.chip_page = 0

# ----------------- 칩 캐러셀 (좌우 버튼 + 현재 페이지 칩들) -----------------
st.markdown('<p class="quick-title">아래 키워드로 물어볼 수도 있겠감</p>', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1, 10, 1])

with c1:
    st.markdown('<div class="arrow">', unsafe_allow_html=True)
    if st.button("‹", key="chip_prev", help="이전"):
        st.session_state.chip_page = (st.session_state.chip_page - 1) % total_pages
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    start = st.session_state.chip_page * VIEW_COUNT
    end = min(start + VIEW_COUNT, len(quick_items))
    st.markdown('<div class="chips">', unsafe_allow_html=True)
    # 칩은 링크지만 target=_self 로 새창 방지, 클릭 후 쿼리파라미터로 즉시 전송 처리
    html = []
    for label in quick_items[start:end]:
        href = f'?chip={quote(label)}'
        html.append(f'<a class="chip-btn" href="{href}" target="_self" title="클릭하면 바로 전송돼요">{label}</a>')
    st.markdown("".join(html), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c3:
    st.markdown('<div class="arrow">', unsafe_allow_html=True)
    if st.button("›", key="chip_next", help="다음"):
        st.session_state.chip_page = (st.session_state.chip_page + 1) % total_pages
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- 인사 말풍선 -----------------
if not st.session_state.welcome_shown:
    st.markdown(f'<div class="chat-bubble assistant-bubble">{WELCOME}</div>', unsafe_allow_html=True)
    st.session_state.welcome_shown = True

# ----------------- 기존 메시지 렌더 -----------------
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    klass = "user-bubble" if msg["role"] == "user" else "assistant-bubble"
    st.markdown(f'<div class="chat-bubble {klass}">{msg["content"]}</div>', unsafe_allow_html=True)

# ----------------- 전송/스트림 함수 -----------------
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

# ----------------- 칩 클릭 처리 (쿼리파라미터 → 즉시 전송) -----------------
qp = st.query_params
if "chip" in qp:
    picked = unquote(qp["chip"])
    send_and_stream(picked)
    # 파라미터 제거(새 탭 X, 같은 탭에서 즉시 전송 후 URL 정리)
    del st.query_params["chip"]

# ----------------- 입력창 -----------------
if prompt := st.chat_input("말감이에게 궁금한걸 말해보세요!"):
    send_and_stream(prompt)

# ----------------- 카드 종료 -----------------
st.markdown('</div>', unsafe_allow_html=True)
