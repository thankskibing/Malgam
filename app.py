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

# ----------------- 환영 메시지 (맨 위 1회) -----------------
if not st.session_state.welcome_shown:
    st.markdown(f'<div class="chat-bubble assistant-bubble">{WELCOME}</div>', unsafe_allow_html=True)
    st.session_state.welcome_shown = True

# ----------------- 대화 렌더 (환영 이후 바로 출력) -----------------
for m in st.session_state.messages:
    if m["role"] == "system":
        continue
    cls = "user-bubble" if m["role"] == "user" else "assistant-bubble"
    st.markdown(f'<div class="{cls} chat-bubble">{m["content"]}</div>', unsafe_allow_html=True)

# ----------------- 퀵칩 (말풍선 아래, 입력창 위로 이동) -----------------
st.markdown('<div class="quick-title">아래 키워드로 물어볼 수도 있겠감</div>', unsafe_allow_html=True)

chips = [
  "👥UX 리서치 설계","📝AI 기획서 작성","🛠️툴 추천",
  "💬프롬프트 가이드","🎨피그마 사용법","📄노션 사용법"
]
html = ['<div class="chips-wrap"><div class="chip-grid">']
for label in chips:
    html.append(f'<div class="chip"><a href="?chip={quote(label)}" target="_self" title="클릭하면 바로 전송돼요">{label}</a></div>')
html.append('</div></div>')
st.markdown("".join(html), unsafe_allow_html=True)

# 칩 클릭 처리
qp = st.query_params
if "chip" in qp:
    picked = unquote(qp["chip"])
    send_and_stream(picked)
    del st.query_params["chip"]

# ----------------- 입력창 -----------------
if txt := st.chat_input("말감이가 질문 기다리는 중!🥔"):
    send_and_stream(txt)

# ----------------- 카드 종료 -----------------
st.markdown('</div>', unsafe_allow_html=True)
