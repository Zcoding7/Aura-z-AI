import streamlit as st
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr
from gtts import gTTS
import base64
from datetime import datetime
import io
from google import genai

api_key = st.secrets.get("GEMINI_API_KEY")
if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = genai.Client()

st.set_page_config(page_title="Voice Assistant", page_icon="🎙️")
st.title("🎙️ Expandable Voice Assistant")

if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "history" not in st.session_state:
    st.session_state.history = []

def speak_web(text):
    st.session_state.history.append(f"🤖 Assistant: {text}")
    tts = gTTS(text=text, lang="en", slow=False)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    b64 = base64.b64encode(fp.read()).decode()
    md = f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}">'
    st.markdown(md, unsafe_allow_html=True)

def ask_ai(prompt, context_type="general"):
    if not api_key:
        return "API key configuration is missing in settings."
    try:
        if context_type == "fact":
            system_instruction = "Tell a random, mind-blowing, verified educational fact. Keep it to one or two short sentences."
        else:
            system_instruction = "Answer this spoken question in one or two short, conversational sentences suitable for text-to-speech reading."
            
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{system_instruction} Input: {prompt}"
        )
        return response.text.strip()
    except Exception as e:
        return f"Brain connection error: {str(e)}"

def handle_command(command):
    if "my name is" in command:
        st.session_state.user_name = command.split("my name is")[-1].strip().title()
        speak_web(f"Hi {st.session_state.user_name}! How can I help you?")
    elif any(greet in command for greet in ["hello", "hi", "hey"]):
        if st.session_state.user_name:
            speak_web(f"Hi {st.session_state.user_name}! How can I help you?")
        else:
            speak_web("Hello! Nice to meet you.")
    elif "date" in command:
        today = datetime.now().strftime("%B %d, %Y")
        speak_web(f"Today is {today}")
    elif "time" in command:
        now = datetime.now().strftime("%I:%M %p")
        speak_web(f"The time is {now}")
    elif "fact" in command:
        ai_fact = ask_ai("Give me a random fact", context_type="fact")
        speak_web(ai_fact)
    elif "joke" in command:
        speak_web("Why did the computer go to the doctor? Because it had a virus!")
    else:
        ai_response = ask_ai(command)
        speak_web(ai_response)

audio_bytes = audio_recorder(text="Tap to talk", recording_color="#e85a4f", neutral_color="#666666")

if audio_bytes:
    recognizer = sr.Recognizer()
    audio_file = io.BytesIO(audio_bytes)
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
        command = recognizer.recognize_google(audio_data, language="en-US").lower()
        st.session_state.history.append(f"👤 You: {command}")
        handle_command(command)
    except sr.UnknownValueError:
        speak_web("I could not understand. Please speak clearly and try again.")
    except Exception:
        speak_web("An error occurred processing your voice. Please try again.")

for chat in reversed(st.session_state.history):
    st.write(chat)
