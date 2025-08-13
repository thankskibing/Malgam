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
.block-container{padding-top:0!important;padding-bottom:120px!important} /* 하단 버튼 공간 */

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

/* 스피너/입력창 */
[data-testid="stSpinner"], [data-testid="stSpinner"] * {color:#FFFFFF !important;}
[data-testid="stSpinner"] svg circle{stroke:#FFFFFF !important;}
[data-testid="stSpinner"] svg path{stroke:#FFFFFF !important; fill:#FFFFFF !important;}
[data-testid="stChatInput"]{background:#F5F1FF!important;border-radius:999px!important;border:1px solid #E0CCFF!important;box-shadow:0 -2px 8px rgba(123,43,255,.15)!important;padding:6px 12px!important;margin-bottom:80px!important}
[data-testid="stChatInput"]:focus-within{border:2px solid #7B2BFF!important;box-shadow:0 0 8px rgba(123,43,255,.35)!important}
[data-testid="stChatInput"] textarea,[data-testid="stChatInput"] input,[data-testid="stChatInput"] div[contenteditable="true"]{border:none!important;outline:none!important;box-shadow:none!important;background:transparent!important}
[data-testid="stChatInput"] button svg path{fill:#7B2BFF!important}

/* 하단 고정 버튼 컨테이너 */
.bottom-button-container {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(15px);
    border-top: 1px solid rgba(123, 43, 255, 0.2);
    padding: 12px 0;
    z-index: 1000;
    box-shadow: 0 -4px 20px rgba(123, 43, 255, 0.15);
}

/* 스크롤 가능한 버튼 래퍼 */
.button-scroll-wrapper {
    overflow-x: auto;
    overflow-y: hidden;
    white-space: nowrap;
    padding: 0 16px;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: thin;
}

/* 스크롤바 스타일링 */
.button-scroll-wrapper::-webkit-scrollbar {
    height: 3px;
}
.button-scroll-wrapper::-webkit-scrollbar-track {
    background: rgba(123, 43, 255, 0.1);
    border-radius: 2px;
}
.button-scroll-wrapper::-webkit-scrollbar-thumb {
    background: rgba(123, 43, 255, 0.4);
    border-radius: 2px;
}
.button-scroll-wrapper::-webkit-scrollbar-thumb:hover {
    background: rgba(123, 43, 255, 0.6);
}

/* 퀵 버튼 스타일 */
.quick-button {
    display: inline-block;
    background: linear-gradient(135deg, #7B2BFF 0%, #A04DFF 100%);
    color: white;
    border: none;
    padding: 10px 16px;
    margin-right: 8px;
    border-radius: 25px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    white-space: nowrap;
    box-shadow: 0 3px 10px rgba(123, 43, 255, 0.3);
    min-width: 100px;
    text-decoration: none;
    border: 1px solid rgba(255, 255, 255, 0.2);
}

.quick-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(123, 43, 255, 0.4);
    background: linear-gradient(135deg, #8A39FF 0%, #B15EFF 100%);
}

.quick-button:active {
    transform: translateY(0);
    box-shadow: 0 2px 8px rgba(123, 43, 255, 0.3);
}

/* 마지막 버튼 마진 */
.quick-button:last-child {
    margin-right: 16px;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
    .bottom-button-container {
        padding: 10px 0;
    }
    .quick-button {
        padding: 8px 12px;
        font-size: 12px;
        min-width: 80px;
        margin-right: 6px;
    }
    .button-scroll-wrapper {
        padding: 0 12px;
    }
}

@media (max-width: 480px) {
    .quick-button {
        padding: 7px 10px;
        font-size: 11px;
        min-width: 70px;
    }
}

/* 버튼 제목 */
.quick-title-fixed {
    position: fixed;
    bottom: 65px;
    left: 16px;
    right: 16px;
    color: #fff;
    font-weight: 800;
    font-size: 16px;
    text-align: center;
    z-index: 999;
    background: rgba(123, 43, 255, 0.9);
    backdrop-filter: blur(10px);
    padding: 6px 12px;
    border-radius: 12px;
    margin: 0;
}

@media (max-width: 768px) {
    .quick-title-fixed {
        font-size: 14px;
        bottom: 55px;
        padding: 4px 8px;
    }
}
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

# ----------------- 하단 고정 스크롤 버튼 -----------------
chip_data = [
    "👥 UX 리서치 설계",
    "📝 AI 기획서 작성", 
    "🛠️ 툴 추천",
    "💬 프롬프트 가이드",
    "🎨 피그마 사용법",
    "📄 노션 사용법",
    "📊 사용자 조사 방법",
    "🔍 경쟁사 분석",
    "📱 모바일 UX 패턴",
    "💡 아이디어 발상법",
    "🏗️ 정보 구조 설계",
    "🎯 페르소나 만들기"
]

# 하단 고정 버튼을 위한 키 상태 관리
if "selected_chip" not in st.session_state:
    st.session_state.selected_chip = None

# JavaScript로 클릭 감지
st.markdown("""
<script>
window.chipClick = function(chipText) {
    window.parent.postMessage({
        type: 'streamlit:chipClicked',
        data: chipText
    }, '*');
}
</script>
""", unsafe_allow_html=True)

# 하단 고정 버튼 HTML 생성
button_html = """
<div class="quick-title-fixed">아래 키워드를 선택해 물어보라감 👇</div>
<div class="bottom-button-container">
    <div class="button-scroll-wrapper" id="buttonWrapper">
"""

for i, chip in enumerate(chip_data):
    # HTML 특수문자 이스케이프
    safe_chip = chip.replace("'", "&#39;").replace('"', '&quot;')
    button_html += f'''
        <button class="quick-button" 
                data-chip="{safe_chip}"
                onclick="
                    const textarea = document.querySelector('[data-testid=stChatInput] textarea');
                    const input = document.querySelector('[data-testid=stChatInput] input');
                    const target = textarea || input;
                    if (target) {{
                        target.value = '{safe_chip}';
                        target.focus();
                        target.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        target.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', bubbles: true }}));
                    }}
                ">
            {chip}
        </button>
    '''

button_html += """
    </div>
</div>
"""

st.markdown(button_html, unsafe_allow_html=True)

# JavaScript를 별도 컴포넌트로 추가
st.components.v1.html("""
<script>
(function() {
    // 터치 스크롤 개선 및 드래그 기능
    function initScrollBehavior() {
        const wrapper = document.getElementById('buttonWrapper');
        if (!wrapper) return;
        
        let isDown = false;
        let startX;
        let scrollLeft;

        // 마우스 이벤트
        wrapper.addEventListener('mousedown', (e) => {
            isDown = true;
            wrapper.style.cursor = 'grabbing';
            startX = e.pageX - wrapper.offsetLeft;
            scrollLeft = wrapper.scrollLeft;
        });

        wrapper.addEventListener('mouseleave', () => {
            isDown = false;
            wrapper.style.cursor = 'grab';
        });

        wrapper.addEventListener('mouseup', () => {
            isDown = false;
            wrapper.style.cursor = 'grab';
        });

        wrapper.addEventListener('mousemove', (e) => {
            if (!isDown) return;
            e.preventDefault();
            const x = e.pageX - wrapper.offsetLeft;
            const walk = (x - startX) * 2;
            wrapper.scrollLeft = scrollLeft - walk;
        });

        // 기본 커서 스타일
        wrapper.style.cursor = 'grab';
    }

    // DOM이 로드된 후 실행
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initScrollBehavior);
    } else {
        initScrollBehavior();
    }
    
    // Streamlit이 다시 렌더링될 때를 대비
    setTimeout(initScrollBehavior, 100);
})();
</script>
""", height=0)

# ----------------- 입력창 -----------------
if txt := st.chat_input("말감이가 질문 기다리는 중!🥔"):
    send_and_stream(txt); st.rerun()

# ----------------- 카드 종료 -----------------
st.markdown('</div>', unsafe_allow_html=True)
