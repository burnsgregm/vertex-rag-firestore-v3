
import streamlit as st
import requests
import json
import uuid
from google.cloud import storage
from google.oauth2 import service_account

API_URL = "https://rag-retrieval-api-v3-mloutt3fdq-uc.a.run.app"
BUCKET_NAME = "test-rag-backend-bucket-v3"

st.set_page_config(page_title="AI Empower V3", layout="wide")
st.title("?? Enterprise Medical AI (V3)")

def get_storage_client():
    if "gcp_service_account" in st.secrets:
        try:
            key_dict = dict(st.secrets["gcp_service_account"])
            creds = service_account.Credentials.from_service_account_info(key_dict)
            return storage.Client(credentials=creds)
        except Exception as e:
            st.error(f"Credential Error: {e}")
            return None
    else:
        try: return storage.Client()
        except: return None

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Tenant Configuration")
    client_id = st.selectbox("Select Client ID", ["tier1_medical_school", "university_b"])
    st.divider()
    st.header("Upload Document")
    uploaded_file = st.file_uploader("PDF/PPTX", type=['pdf', 'pptx'])
    if uploaded_file and st.button("Ingest"):
        client = get_storage_client()
        if client:
            with st.spinner("Uploading..."):
                try:
                    bucket = client.bucket(BUCKET_NAME)
                    blob = bucket.blob(f"uploads/{client_id}/{uploaded_file.name}")
                    blob.upload_from_file(uploaded_file)
                    st.success("Upload Complete!")
                except Exception as e:
                    st.error(f"Failed: {e}")

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.spinner("Consulting V3 Knowledge Base..."):
        try:
            response = requests.post(API_URL, json={
                "query": prompt,
                "client_id": client_id,
                "session_id": st.session_state.session_id
            })
            data = response.json()
            answer = data.get("answer", "Error")
            st.chat_message("assistant").write(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
        except Exception as e:
            st.error(f"Connection Failed: {e}")
