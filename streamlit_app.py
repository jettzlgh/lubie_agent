import streamlit as st
from agent2 import process_user_request  # <-- your existing back-end code

def main():
    st.title("Bonjour, je suis l'assistant de My Lubie !")
    st.write("Posez votre question ci-dessous :")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Votre question"):
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        print(f"stmessage is : {st.session_state.messages}")
        ai_response = process_user_request(prompt, st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
        with st.chat_message("assistant"):
            st.markdown(ai_response)


    # for message in st.session_state.messages:
    #     with st.chat_message(message["role"]):
    #         st.markdown(message["content"])

    # if st.button("Envoyer"):
    #     if user_input.strip():
    #         # 1) Add user message to chat history
    #         st.session_state.history.append(("user", user_input))

    #         # 2) Process user request (calling your AI agent)
    #         ai_response = process_user_request(user_input)

    #         # 3) Add AI response to chat history
    #         st.session_state.history.append(("assistant", ai_response))


    # # Display conversation with custom alignment and colors
    # for role, content in st.session_state.history:
    #     if role == "user":
    #         st.markdown(
    #             f"""
    #             <div style="text-align: right; background-color: #C2F9FF;
    #                         padding: 10px; margin: 10px; border-radius: 10px;">
    #                 <strong>Vous:</strong> {content}
    #             </div>
    #             """,
    #             unsafe_allow_html=True
    #         )
    #     else:  # assistant
    #         st.markdown(
    #             f"""
    #             <div style="text-align: left; background-color: #FFD2A5;
    #                         padding: 10px; margin: 10px; border-radius: 10px;">
    #                 <strong>Assistant:</strong> {content}
    #             </div>
    #             """,
    #             unsafe_allow_html=True
    #         )

if __name__ == "__main__":
    main()
