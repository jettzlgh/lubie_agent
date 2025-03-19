import streamlit as st
from agent2 import process_user_request  # <-- your existing back-end code

def main():
    st.title("Bonjour, je suis l'assistant de My Lubie !")
    st.write("Posez votre question ci-dessous :")
    st.write("Mise à jour 19/03/2025")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if st.sidebar.button("Reset Chat"):
        st.session_state.messages = []
        # Adding or changing a query param triggers a re-run
        st.query_params.clear()
        # st.stop()

    # -- DISPLAY CHAT HISTORY --
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # -- USER INPUT --
    if prompt := st.chat_input("Votre question"):
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Process AI response
        print(len(st.session_state.messages))
        ai_response = process_user_request(prompt, st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": ai_response})

        # Display AI response
        with st.chat_message("assistant"):
            st.markdown(ai_response)

if __name__ == "__main__":
    main()
