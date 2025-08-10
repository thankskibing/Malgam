from openai import OpenAI
import streamlit as st

st.set_page_config(page_title="말감 챗봇", page_icon="🥔", layout="centered")

# ---------- CSS ----------
st.markdown("""
<style>
/* 앱 배경(보라 그라데이션) */
.stApp {
  background: linear-gradient(180deg, #7B2BFF 0%, #8A39FF 35%, #A04DFF 100%) !important;
}

/* 중앙 컨테이너를 카드처럼 */
.main > div { padding-top: 0 !important; }
.block-container {
  padding-top: 16px !important;
}
.chat-card {
  background: #FFFFFF;
  border-radius: 24px;
  box-shadow: 0 12px 40px rgba(0,0,0,0.12);
  padding: 20px 16px 8px 16px;
}

/* 말풍선 */
.chat-bubble {
  display: block;
  clear: both;
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 16px;
  margin: 8px 0;
  line-height: 1.4;
  white-space: pre-wrap;
  word-break: break-word;
}
.user-bubble { background-color: #DCF8C6; float: right; text-align: right; }
.assistant-bubble { background-color: #F1F0F0; float: left; text-align: left; }

/* 빠른 답변(칩) */
.quick-row {
  display: flex; gap: 10px; flex-wrap: wrap;
  padding: 8px 0 0 0;
}
.quick-chip {
  background: #F3E8FF;             /* 연보라 */
  border: 1px solid #E5D4FF;
  border-radius: 999px;
  padding: 8px 14px;
  font-size: 14px;
  cursor: pointer;
  user-select: none;
}
.quick-chip:hover { filter: brightness(0.96); }

/* 입력창을 카드 하단에 더 붙어 보이게 */
[data-testid="stChatInput"] {
  margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)

# ---------- 헤더 / 로고 ----------
col1, col2 = st.columns([1,8])
with col1:
    st.image("logo.png", width=64)
with col2:
    st.markdown("<h2 style='color:white;margin:8px 0 0'>말감 챗봇</h2>", unsafe_allow_html=True)

# ---------- 카드 래퍼 ----------
st.markdown('<div class="chat-card">', unsafe_allow_html=True)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "openai_model" not in st.session_state:
    st.session_state.openai_model = "gpt-3.5-turbo"

system_message = '''
#지침: 너는 ui/ux 기획, 디자인, 리서처 업무를 도와주는 이름은 말감이야.
너는 피그마나 디자인, ai 관련한 질문을 받아주고 고민 상담도 들어줘
너는 항상 감으로 문장을 끝내주고 항상 친근하게 대답해줘.
영어로 질문을 받아도 무조건 한글로 답변해줘.
한글이 아닌 답변일 때는 다시 생각해서 꼭 한글로 만들어줘
모든 답변 끝에 답변에 맞는 이모티콘도 추가해줘
'''
welcome_text = "안녕하세요! 저는 여러분을 도와줄 ‘말하는 감자 말감이’예요. 궁금한 점이나 고민이 있다면 자유롭게 물어보라감!😊"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": system_message},
        {"role": "assistant", "content": welcome_text}
    ]

# ---------- 빠른 답변 칩 ----------
quick_items = ["AI 기획서 작성", "툴 추천", "아이디어 확장", "AI 리서치"]
st.markdown('<div class="quick-row">', unsafe_allow_html=True)
qcols = st.columns(len(quick_items))
for i, q in enumerate(quick_items):
    # HTML 칩 + form 버튼 조합 (Streamlit 버튼만 쓰면 스타일 제한)
    with qcols[i]:
        if st.button(q, key=f"quick_{i}", help="클릭하면 바로 전송돼요"):
            st.session_state.selected_quick = q
st.markdown('</div>', unsafe_allow_html=True)

# ---------- 기존 대화 렌더 ----------
for msg in st.session_state.messages[1:]:
    role, text = msg["role"], msg["content"]
    klass = "user-bubble" if role == "user" else "assistant-bubble"
    st.markdown(f'<div class="chat-bubble {klass}">{text}</div>', unsafe_allow_html=True)

# ---------- 전송 함수 ----------
def send_and_stream(user_text: str):
    st.session_state.messages.append({"role": "user", "content": user_text})
    st.markdown(f'<div class="chat-bubble user-bubble">{user_text}</div>', unsafe_allow_html=True)

    stream = client.chat.completions.create(
        model=st.session_state.openai_model,
        messages=st.session_state.messages,
        stream=True,
    )
    assistant_text = ""
    for chunk in stream:
        assistant_text += chunk.choices[0].delta.content or ""

    st.markdown(f'<div class="chat-bubble assistant-bubble">{assistant_text}</div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role": "assistant", "content": assistant_text})

# 칩이 눌렸다면 즉시 전송
if "selected_quick" in st.session_state:
    send_and_stream(st.session_state.selected_quick)
    del st.session_state.selected_quick

# ---------- 입력창 ----------
if prompt := st.chat_input("말감이에게 궁금한걸 말해보세요!"):
    send_and_stream(prompt)

# 카드 끝
st.markdown('</div>', unsafe_allow_html=True)
