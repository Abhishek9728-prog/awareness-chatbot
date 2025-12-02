import streamlit as st
from dotenv import load_dotenv
from src.helper import download_hugging_face_embeddings
from src.prompt import system_prompt
from src.audio_helper import audio_to_text_mic, text_to_audio

from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import os

# -------------------------------
# 🌐 Load environment
# -------------------------------
load_dotenv()

# -------------------------------
# ⚙️ Page Configuration
# -------------------------------
st.set_page_config(page_title="🛡️ Fraud Assistant", page_icon="🎙️", layout="wide")
st.title("🎧 Fraud Prevention Chatbot")

# -------------------------------
# 🧾 Sidebar Information
# -------------------------------
with st.sidebar:
    st.header("About")
    st.info("Voice-enabled Fraud Prevention Chatbot using LangChain + FAISS + Groq.")
    st.warning("⚠️ For educational use only. Always verify with official authorities before taking action.")

    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()

st.subheader("🚨 Check Spam Message")

st.markdown("""
Use the spam detection tool to verify suspicious messages:

👉 **[Open Spam Detector](https://spam-detector-cf42.onrender.com)**  
""")

# -------------------------------
# 🔍 Initialize RAG Chain (cached)
# -------------------------------
@st.cache_resource
def initialize_rag_chain():
    try:
        embeddings = download_hugging_face_embeddings()
        
        # Check if FAISS index exists
        if not os.path.exists("faiss_index"):
            st.error("❌ FAISS index not found! Please run store_index.py first.")
            return None
            
        vectorstore = FAISS.load_local(
            "faiss_index", 
            embeddings, 
            allow_dangerous_deserialization=True
        )
        retriever = vectorstore.as_retriever(
            search_type="similarity", 
            search_kwargs={"k": 3}
        )
        
        # Check for GROQ API key
        if not os.getenv("GROQ_API_KEY"):
            st.error("❌ GROQ_API_KEY not found in environment variables!")
            return None
            
        llm = ChatGroq(
            model="llama-3.3-70b-versatile", 
            temperature=0
        )
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])
        
        # Helper function to format retrieved documents
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        # Build RAG chain using LangChain Expression Language (LCEL)
        rag_chain = (
            {
                "context": retriever | format_docs,
                "input": RunnablePassthrough()
            }
            | prompt
            | llm
            | StrOutputParser()
        )
        
        return rag_chain
        
    except Exception as e:
        st.error(f"❌ Error initializing RAG chain: {str(e)}")
        return None

rag_chain = initialize_rag_chain()

# Check if initialization was successful
if rag_chain is None:
    st.stop()

# -------------------------------
# 💬 Chat History
# -------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message['content'])

# -------------------------------
# 🎤 Audio Input Section
# -------------------------------
st.subheader("🎙️ Ask Your Question")

input_method = st.radio(
    "Choose how you want to ask your question:",
    ["⌨️ Type Manually", "🎤 Speak via Microphone"],
    horizontal=True
)

user_input = None

# --- Option 1: Manual Text Input ---
if input_method == "⌨️ Type Manually":
    user_input = st.chat_input("Type your question here...")

# --- Option 2: Microphone Input ---
elif input_method == "🎤 Speak via Microphone":
    st.info("Click the button below and speak clearly for 5 seconds.")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        record_button = st.button("🎙️ Start Recording", type="primary")
    
    if record_button:
        with st.spinner("🎤 Listening... please speak clearly"):
            try:
                user_input = audio_to_text_mic(duration=5)
                if user_input and not user_input.startswith("❌") and not user_input.startswith("⚠️"):
                    st.success(f"🗣️ You said: **{user_input}**")
                else:
                    st.error(user_input)
                    user_input = None
            except Exception as e:
                st.error(f"❌ Recording error: {str(e)}")
                user_input = None

# -------------------------------
# 🤖 Process the User Input
# -------------------------------
if user_input:
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate bot response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Analyzing your question..."):
            try:
                # Invoke the RAG chain with user input
                bot_reply = rag_chain.invoke(user_input)
                
                st.markdown(bot_reply)
                
                # Add assistant message to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
                
                # -------------------------------
                # 🔊 Generate Audio Reply
                # -------------------------------
                with st.spinner("🔊 Generating audio reply..."):
                    try:
                        audio_path = text_to_audio(bot_reply)
                        with open(audio_path, "rb") as f:
                            audio_bytes = f.read()
                        st.audio(audio_bytes, format="audio/mp3")
                    except Exception as audio_error:
                        st.warning(f"⚠️ Could not generate audio: {str(audio_error)}")
                        
            except Exception as e:
                error_msg = f"❌ Error generating response: {str(e)}"
                st.error(error_msg)
                st.session_state.chat_history.append({"role": "assistant", "content": error_msg})