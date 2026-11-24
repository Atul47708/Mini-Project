import streamlit as st
import requests
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

# Page Configuration
st.set_page_config(
    page_title="Aura — Multimodal AI Companion",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# Custom Dark Theme & Polished Styling
st.markdown("""
<style>
    /* Dark Theme Global Styling */
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    }
    
    /* Header Card */
    .hero-header {
        background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-radius: 14px;
        padding: 22px 28px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    .hero-title {
        font-size: 26px;
        font-weight: 700;
        color: #c4b5fd;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .hero-subtitle {
        font-size: 14px;
        color: #94a3b8;
        line-height: 1.5;
    }

    /* Message Styling */
    .user-bubble {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 12px;
        color: #f1f5f9;
    }
    .assistant-bubble {
        background: #131b2e;
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 14px;
        color: #e2e8f0;
    }
    
    /* Modality Badges */
    .modality-badge {
        display: inline-block;
        font-size: 11px;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 12px;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-text { background-color: #3b82f6; color: white; }
    .badge-image { background-color: #10b981; color: white; }
    .badge-audio { background-color: #f59e0b; color: white; }
    .badge-document { background-color: #8b5cf6; color: white; }

    /* Source Reference Citation Card */
    .source-box {
        background: #0f172a;
        border-left: 3px solid #8b5cf6;
        padding: 10px 14px;
        margin-top: 10px;
        border-radius: 6px;
        font-size: 13px;
        color: #cbd5e1;
    }
    
    /* Safety Notice Box */
    .disclaimer-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(148, 163, 184, 0.2);
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 12px;
        color: #94a3b8;
        margin-top: 16px;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "current_conversation_id" not in st.session_state:
    st.session_state.current_conversation_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversations_list" not in st.session_state:
    st.session_state.conversations_list = []
if "indexed_documents" not in st.session_state:
    st.session_state.indexed_documents = []

# API Client Functions
def check_api_health() -> Dict[str, Any]:
    try:
        res = requests.get(f"{API_BASE_URL}/health", timeout=3)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {"status": "offline", "database": "unknown", "gemini_api_configured": False}

def fetch_conversations():
    try:
        res = requests.get(f"{API_BASE_URL}/conversations", timeout=4)
        if res.status_code == 200:
            st.session_state.conversations_list = res.json()
    except Exception:
        st.session_state.conversations_list = []

def fetch_conversation_messages(conversation_id: str):
    try:
        res = requests.get(f"{API_BASE_URL}/conversations/{conversation_id}", timeout=5)
        if res.status_code == 200:
            data = res.json()
            st.session_state.messages = data.get("messages", [])
    except Exception as e:
        st.error(f"Failed to load conversation: {e}")

def create_new_conversation():
    try:
        res = requests.post(f"{API_BASE_URL}/conversations", json={"title": "New Conversation"}, timeout=4)
        if res.status_code == 200:
            new_conv = res.json()
            st.session_state.current_conversation_id = new_conv["id"]
            st.session_state.messages = []
            fetch_conversations()
    except Exception as e:
        st.error(f"Failed to create conversation: {e}")

def delete_conversation(conversation_id: str):
    try:
        res = requests.delete(f"{API_BASE_URL}/conversations/{conversation_id}", timeout=4)
        if res.status_code == 200:
            if st.session_state.current_conversation_id == conversation_id:
                st.session_state.current_conversation_id = None
                st.session_state.messages = []
            fetch_conversations()
    except Exception as e:
        st.error(f"Failed to delete conversation: {e}")

def fetch_indexed_documents():
    try:
        res = requests.get(f"{API_BASE_URL}/documents", timeout=4)
        if res.status_code == 200:
            st.session_state.indexed_documents = res.json()
    except Exception:
        st.session_state.indexed_documents = []

def upload_rag_document(file):
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        data = {}
        if st.session_state.current_conversation_id:
            data["conversation_id"] = st.session_state.current_conversation_id

        res = requests.post(f"{API_BASE_URL}/upload/document", files=files, data=data, timeout=30)
        if res.status_code == 200:
            doc_data = res.json()
            st.sidebar.success(f"Indexed '{doc_data['filename']}' ({doc_data['chunk_count']} chunks)")
            fetch_indexed_documents()
        else:
            err = res.json().get("detail", res.text)
            st.sidebar.error(f"Upload error: {err}")
    except Exception as e:
        st.sidebar.error(f"Failed to upload document: {e}")

# Initial Load
fetch_conversations()
fetch_indexed_documents()
health = check_api_health()

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### ✨ Aura Studio")
    st.caption("Personal Multimodal AI Companion")

    # System Status Indicator
    status_color = "🟢" if health["status"] == "healthy" else "🟡" if health["status"] == "degraded" else "🔴"
    gemini_status = "Connected" if health.get("gemini_api_configured") else "Offline Fallback"
    db_mode = "MySQL" if "mysql" in health.get("database", "").lower() else "SQLite"

    st.markdown(
        f"<div style='background:#1e293b; padding:10px 14px; border-radius:8px; font-size:12px; margin-bottom:14px;'>"
        f"<b>Backend:</b> {status_color} {health['status'].upper()}<br/>"
        f"<b>Database:</b> {db_mode}<br/>"
        f"<b>AI Engine:</b> {gemini_status}"
        f"</div>",
        unsafe_allow_html=True
    )

    if st.button("➕ New Conversation", use_container_width=True, type="primary"):
        create_new_conversation()
        st.rerun()

    # Session Selector
    st.markdown("---")
    st.markdown("#### 💬 Conversations")
    if st.session_state.conversations_list:
        for conv in st.session_state.conversations_list:
            col1, col2 = st.columns([0.82, 0.18])
            is_active = conv["id"] == st.session_state.current_conversation_id
            btn_label = f"{'▸ ' if is_active else ''}{conv['title'][:22]}"
            if col1.button(btn_label, key=f"conv_{conv['id']}", use_container_width=True):
                st.session_state.current_conversation_id = conv["id"]
                fetch_conversation_messages(conv["id"])
                st.rerun()
            if col2.button("🗑️", key=f"del_{conv['id']}", help="Delete conversation"):
                delete_conversation(conv["id"])
                st.rerun()
    else:
        st.caption("No conversations yet. Start one above!")

    # Document RAG Center
    st.markdown("---")
    st.markdown("#### 📄 Document Library (RAG)")
    rag_file = st.file_uploader(
        "Upload PDF, DOCX, or TXT for Grounded Knowledge",
        type=["pdf", "docx", "txt", "md"],
        key="rag_uploader"
    )
    if rag_file is not None:
        if st.button("Index Document", key="btn_index_doc", use_container_width=True):
            with st.spinner("Parsing, chunking, and embedding document..."):
                upload_rag_document(rag_file)
                st.rerun()

    # Display currently indexed documents
    if st.session_state.indexed_documents:
        st.markdown(f"**Indexed Knowledge ({len(st.session_state.indexed_documents)}):**")
        for doc in st.session_state.indexed_documents[:5]:
            st.caption(f"• `{doc['filename']}` ({doc['chunk_count']} chunks)")
    else:
        st.caption("No documents indexed yet.")

    # Settings & Controls
    st.markdown("---")
    st.markdown("#### ⚙️ Companion Settings")
    use_rag_toggle = st.toggle("Enable RAG Context Retrieval", value=True)
    voice_toggle = st.toggle("Synthesize Voice Output (TTS)", value=False)

    st.markdown("""
    <div class="disclaimer-card">
        <b>Safety Notice:</b> Aura is an empathetic AI companion, not a licensed healthcare provider. If you are experiencing acute distress, call or text <b>988</b> (US/CA) or your local crisis helpline.
    </div>
    """, unsafe_allow_html=True)


# ==================== MAIN CHAT AREA ====================
# Hero Header
st.markdown("""
<div class="hero-header">
    <div class="hero-title">✨ Aura — Secure Multimodal AI Companion</div>
    <div class="hero-subtitle">
        Empathetic conversational companion equipped with image reasoning, voice synthesis, grounded RAG document intelligence, and privacy guardrails.
    </div>
</div>
""", unsafe_allow_html=True)

# Display Messages
if st.session_state.messages:
    for msg in st.session_state.messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        input_modality = msg.get("input_modality", "text")
        output_modality = msg.get("output_modality", "text")
        media_url = msg.get("media_url")
        sources = msg.get("sources", [])

        if role == "user":
            with st.chat_message("user"):
                badge_class = f"badge-{input_modality}"
                st.markdown(f"<span class='modality-badge {badge_class}'>{input_modality}</span>", unsafe_allow_html=True)
                st.markdown(content)
                if media_url and ("jpg" in media_url or "png" in media_url or "webp" in media_url):
                    if Path(media_url).exists():
                        st.image(media_url, width=320)
        else:
            with st.chat_message("assistant", avatar="✨"):
                badge_class = "badge-audio" if output_modality == "audio" else "badge-text"
                st.markdown(f"<span class='modality-badge {badge_class}'>AI Companion • {output_modality}</span>", unsafe_allow_html=True)
                st.markdown(content)

                # Audio Player for TTS
                if media_url and "audio" in output_modality:
                    # Construct full audio URL
                    audio_full_url = f"{API_BASE_URL}{media_url}" if media_url.startswith("/") else media_url
                    st.audio(audio_full_url)

                # RAG Sources Collapsible Card
                if sources:
                    with st.expander(f"📚 Grounded Knowledge References ({len(sources)} sources)"):
                        for idx, src in enumerate(sources):
                            st.markdown(
                                f"<div class='source-box'>"
                                f"<b>Source {idx+1}:</b> <code>{src.get('filename')}</code> (Chunk {src.get('chunk_index')}) — <i>Relevance: {src.get('relevance_score', 0):.2f}</i><br/>"
                                f"\"{src.get('content')}\""
                                f"</div>",
                                unsafe_allow_html=True
                            )
else:
    # Empty State Greeting
    st.info("👋 Welcome! You can talk freely with Aura. Share your thoughts, upload an image or audio file below, or ask questions about your uploaded documents.")

# Multimodal Input Expanders
col_img, col_aud = st.columns(2)
with col_img:
    with st.expander("📷 Attach an Image (JPG/PNG/WEBP)"):
        uploaded_image = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png", "webp"], key="chat_img_uploader")
        if uploaded_image:
            st.image(uploaded_image, caption="Attached Image Preview", width=220)

with col_aud:
    with st.expander("🎙️ Attach an Audio Message (MP3/WAV)"):
        uploaded_audio = st.file_uploader("Upload Audio", type=["mp3", "wav", "m4a", "ogg"], key="chat_aud_uploader")
        if uploaded_audio:
            st.audio(uploaded_audio)

# Chat Input Bar
prompt = st.chat_input("Message Aura... (Share your thoughts or ask a question)")

if prompt or uploaded_image or uploaded_audio:
    user_text = prompt or "Can you analyze this attachment for me?"

    # Display user message immediately in UI
    with st.chat_message("user"):
        st.markdown(user_text)

    # Prepare Multimodal Request
    files = {}
    data = {
        "message": user_text,
        "conversation_id": st.session_state.current_conversation_id or "",
        "use_rag": "true" if use_rag_toggle else "false",
        "generate_speech": "true" if voice_toggle else "false"
    }

    if uploaded_image:
        files["image"] = (uploaded_image.name, uploaded_image.getvalue(), uploaded_image.type)
    if uploaded_audio:
        files["audio"] = (uploaded_audio.name, uploaded_audio.getvalue(), uploaded_audio.type)

    with st.chat_message("assistant", avatar="✨"):
        with st.spinner("Aura is reflecting..."):
            try:
                if files:
                    # Call multimodal endpoint
                    response = requests.post(f"{API_BASE_URL}/chat/multimodal", data=data, files=files, timeout=45)
                else:
                    # Call standard chat endpoint
                    chat_json = {
                        "conversation_id": st.session_state.current_conversation_id,
                        "message": user_text,
                        "use_rag": use_rag_toggle,
                        "generate_speech": voice_toggle
                    }
                    response = requests.post(f"{API_BASE_URL}/chat", json=chat_json, timeout=30)

                if response.status_code == 200:
                    res_data = response.json()
                    st.session_state.current_conversation_id = res_data.get("conversation_id")
                    asst_text = res_data.get("assistant_response", "")
                    audio_url = res_data.get("audio_url")
                    sources = res_data.get("sources", [])

                    st.markdown(asst_text)

                    if audio_url:
                        full_audio_url = f"{API_BASE_URL}{audio_url}" if audio_url.startswith("/") else audio_url
                        st.audio(full_audio_url)

                    if sources:
                        with st.expander(f"📚 Grounded Knowledge References ({len(sources)} sources)"):
                            for idx, src in enumerate(sources):
                                st.markdown(
                                    f"<div class='source-box'>"
                                    f"<b>Source {idx+1}:</b> <code>{src.get('filename')}</code> (Chunk {src.get('chunk_index')}) — <i>Relevance: {src.get('relevance_score', 0):.2f}</i><br/>"
                                    f"\"{src.get('content')}\""
                                    f"</div>",
                                    unsafe_allow_html=True
                                )

                    # Refresh conversation list and messages
                    fetch_conversations()
                    if st.session_state.current_conversation_id:
                        fetch_conversation_messages(st.session_state.current_conversation_id)

                else:
                    err_msg = response.json().get("detail", response.text)
                    st.error(f"Error from companion: {err_msg}")

            except Exception as e:
                st.error(f"Failed to communicate with Aura backend: {e}")
