import streamlit as st
import time
import os
import requests
import json

# --- Configuration ---
PAGE_TITLE = "Mindful Support"
PAGE_ICON = "🏈"
CHATBOT_NAME = "MindfulBot"
USER_NAME = "You"
WELCOME_MESSAGE = f"""
Welcome to {CHATBOT_NAME}, your safe space to talk. I'm here to listen and offer support.
Please remember I'm an AI and not a substitute for professional help.
If you're in crisis, please seek immediate assistance.
"""
DISCLAIMER = f"""
**Disclaimer:** {CHATBOT_NAME} is an AI and does not provide medical advice.
It is intended for informational and support purposes only.
"""

SESSION_JSON_PATH = "session_data.json"

# --- Load Custom System Prompt ---
with open("prompt.txt", "r", encoding="utf-8") as file:
    SYSTEM_PROMPT = file.read().strip()

# --- Groq API Setup ---
GROQ_API_KEY = os.getenv("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")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

# --- Helper Functions ---
def display_disclaimer():
    st.markdown(DISCLAIMER, unsafe_allow_html=True)

def display_welcome_message():
    st.markdown(WELCOME_MESSAGE, unsafe_allow_html=True)

def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})

def clear_chat():
    st.session_state.messages = []
    st.session_state.session_id = time.time()
    st.session_state.summary = ""
    init_session_file()

def init_session_file():
    data = {
        "session_id": st.session_state.session_id,
        "chat": [],
        "summary": ""
    }
    with open(SESSION_JSON_PATH, "w") as f:
        json.dump(data, f, indent=4)

def update_session_file(user_input, new_summary, assistant_reply):
    with open(SESSION_JSON_PATH, "r") as f:
        data = json.load(f)

    data["chat"].append({
        "user_input": user_input,
        "assistant_reply": assistant_reply
    })
    data["summary"] = new_summary

    with open(SESSION_JSON_PATH, "w") as f:
        json.dump(data, f, indent=4)

def get_model_input():
    if not os.path.exists(SESSION_JSON_PATH):
        return ""

    with open(SESSION_JSON_PATH, "r") as f:
        data = json.load(f)

    return json.dumps({
        "summarised_text": data.get("summary", ""),
        "newQuestion": data["chat"][-1]["user_input"] if data["chat"] else ""
    })

def get_response_from_groq(model_input):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": SYSTEM_PROMPT + "\n\ninput text = " + model_input + "\n\noutput text ="}
        ],
        "temperature": 0.7,
        "max_tokens": 300
    }
    response = requests.post(GROQ_API_URL, headers=headers, json=payload)
    result = response.json()
    if "choices" not in result:
        return "Sorry, something went wrong."
    return result["choices"][0]["message"]["content"].strip()

# --- Main App Function ---
def main():
    st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON)
    st.title(PAGE_TITLE)

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.session_id = time.time()
        st.session_state.summary = ""
        init_session_file()

    with st.sidebar:
        display_welcome_message()
        st.button("Start New Conversation", on_click=clear_chat, key="new_chat_button")
        display_disclaimer()
        with st.expander("Mental Health Resources"):
            st.markdown(
                """
                Here are some helpful resources:
                * [Advancing Mental Healthcare in India](https://mohfw.gov.in/?q=pressrelease-206#:~:text=WHO%20estimates%20that%20the%20burden,estimated%20at%20USD%201.03%20trillion.)
                * [W.H.O Mental Health](https://www.who.int/health-topics/mental-health#tab=tab_1)
                * [The Mental Health Association](https://www.mhanational.org/)
                """
            )
        st.markdown(f"Session ID: {st.session_state.session_id}")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)

    if prompt := st.chat_input("Type your message here...", key="chat_input"):
        add_message(USER_NAME, prompt)
        with st.chat_message(USER_NAME):
            st.markdown(prompt, unsafe_allow_html=True)

        update_session_file(prompt, st.session_state.summary, "")
        model_input = get_model_input()
        model_output = get_response_from_groq(model_input)

        new_response = model_output.split(",,")

        if len(new_response) >= 2:
            new_summary = new_response[0].replace("new_sumary:", "").strip()
            assistant_reply = new_response[-1].replace("newAnswer:", "").strip()
        else:
            new_summary = st.session_state.summary
            assistant_reply = model_output.strip()

        st.session_state.summary = new_summary
        update_session_file(prompt, new_summary, assistant_reply)

        add_message(CHATBOT_NAME, assistant_reply)
        with st.chat_message(CHATBOT_NAME):
            st.markdown(assistant_reply, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
