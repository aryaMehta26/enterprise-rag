import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000/query")

st.title("Enterprise RAG System")

question = st.text_input("Ask a question:")
source = st.selectbox("Source", ["all", "PDF", "Wikipedia"])

if st.button("Submit"):
    if not question:
        st.warning("Please enter a question.")
    else:       
        with st.spinner("Querying..."):
            resp = requests.post(API_URL, json={"question": question, "source": source})
            if resp.status_code == 200:
                data = resp.json()
                st.markdown(f"**Answer:** {data['result']}")
                st.markdown("**Sources:**")
                for src in data["sources"]:
                    st.write(src)
            else:                                                                                              
                st.error(f"Error: {resp.text}") 