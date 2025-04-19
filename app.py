from openai import OpenAI
import streamlit as st

st.set_page_config(page_title="탐방GO 챗봇")
st.image("logo.png", width=100)
st.title("탐방GO 챗봇")
# st.caption("안녕하세요! 저는 탐방GO의 친구봇 ‘고고’예요. 어디로 갈지 고민이라면 언제든 물어보세요! 😊")

# ——— CSS 인라인 ———
st.markdown(
    """
    <style>
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
    /* 오른쪽(유저) 말풍선 */
    .user-bubble {
      background-color: #DCF8C6;
      float: right;
      text-align: right;
    }
    /* 왼쪽(어시스턴트) 말풍선 */
    .assistant-bubble {
      background-color: #F1F0F0;
      float: left;
      text-align: left;
    }
    </style>
    """,
    unsafe_allow_html=True
)

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "model" not in st.session_state:
    st.session_state.model = "gpt-3.5-turbo"
if "openai_model" not in st.session_state:
    st.session_state.openai_model = "gpt-3.5-turbo"

system_message = '''
너의 이름은 GO봇이야.
너는 장소에 대한 정보를 추천해주고 활동을 추천해주는 역할을 해
너는 항상 존댓말을 하는 챗봇이야. 다나까나 요 같은 높임말로 절대로 끝내줘
항상 존댓말로 친근하게 대답해줘.
영어로 질문을 받아도 무조건 한글로 답변해줘.
한글이 아닌 답변일 때는 다시 생각해서 꼭 한글로 만들어줘
모든 답변 끝에 답변에 맞는 이모티콘도 추가해줘
'''
welcome_text = "  안녕하세요! 저는 탐방GO의 친구봇 ‘고고’예요.<br> 어디로 갈지 고민이라면 언제든 물어보세요!😊"

if "messages" not in st.session_state:
    # st.session_state.messages = [{"role": "system", "content": system_message}]
     st.session_state.messages = [
        {"role": "system",    "content": system_message},
        {"role": "assistant", "content": welcome_text}
    ]

for msg in st.session_state.messages[1:]:
    role = msg["role"]
    text = msg["content"]
    if role == "user":
        st.markdown(f'<div class="chat-bubble user-bubble">{text}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-bubble assistant-bubble">{text}</div>', unsafe_allow_html=True)

# ——— 사용자 입력 및 응답 처리 ———
if prompt := st.chat_input("무엇을 도와드릴까요?😊"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.markdown(
        f'<div class="chat-bubble user-bubble">{prompt}</div>',
        unsafe_allow_html=True
    )

    stream = client.chat.completions.create(
        model=st.session_state.openai_model,
        messages=st.session_state.messages,
        stream=True,
    )

    assistant_text = ""
    for chunk in stream:
        assistant_text += chunk.choices[0].delta.content or ""

    st.markdown(
        f'<div class="chat-bubble assistant-bubble">{assistant_text}</div>',
        unsafe_allow_html=True
    )

    st.session_state.messages.append(
        {"role": "assistant", "content": assistant_text}
    )
