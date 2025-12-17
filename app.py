from openai import OpenAI
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

st.set_page_config (page_title="Streamlit Chat", page_icon=":speech_balloon:")
st.title("Chatbot")

# Session state setup
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown =  False
if "messages" not in st.session_state: 
    st.session_state.messages = []
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False

def complete_setup():
    st.session_state.setup_complete = True
def show_feedback():
    st.session_state.feedback_shown = True

# If the setup_complete state var is false display following form, allowing the user to input details
if not st.session_state.setup_complete:    
    #### Interviewee Context Information Boxes ####
    st.subheader("Personal information", divider="rainbow")

    # Checking if key exists in session state, if not session state for var has not been initialized. Key is then created and its default value to empty string
    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "experience" not in st.session_state:
        st.session_state["experience"] = ""
    if "skills" not in st.session_state:
        st.session_state["skills"] = ""

    st.session_state["name"] = st.text_input(label = "Name", max_chars = 40, value = st.session_state["name"], placeholder = "Enter your name") 
    st.session_state["experience"] = st.text_area(label = "Experience", value = st.session_state["experience"], height = None, max_chars = 200, placeholder= "Describe your experience")
    st.session_state["skills"] = st.text_area(label = "Skills", value = st.session_state["skills"], height = None, max_chars = 200, placeholder = "List your skills")

    # Message formatting with placeholders
    st.write(f"**Your Name**: {st.session_state["name"]}")
    st.write(f"**Your Experience**: {st.session_state["experience"]}")
    st.write(f"**Your Skills**: {st.session_state["skills"]}")

    #### Chosen Company and Position Information ####
    st.subheader("Company and Position", divider= "rainbow")

    # Checking if key exists in session state, if not session state for var has not been initialized. Key is then created and a default value is assigned
    if "level" not in st.session_state:
        st.session_state["level"] = "Junior"
    if "position" not in st.session_state:
        st.session_state["position"] = "Data Scientist"
    if "company" not in st.session_state:
        st.session_state["company"] = "Amazon"

    # We organize the options into two columns
    col1, col2 = st.columns(2)
    with col1:
        st.session_state["level"] = st.radio(
        "Choose level", 
        key = "visibility", # key parameter helps maintain widget state across interactions
        options = ["Junior", "Mid-level", "Senior"],
        )
    with col2:
        st.session_state["position"] = st.selectbox(
        "Choose a position",
        ("Data Scientist", "Data Engineer", "ML Engineer", "BI Analyst", "Financial Analyst")
        )
    st.session_state["company"] = st.selectbox(
        "Choose a Company",
        ("Amazon", "Meta", "Udemy", "365 Company", "Nestle", "LinkedIn", "Spotify")
        )

    st.write(f"**Your Information**: {st.session_state["level"]} {st.session_state["position"]} at {st.session_state["company"]}")

    # Button to call the complete setup function, setting the setup complete session state to true causing the form to dissapear
    if st.button("Start Interview", on_click = complete_setup):
        st.write("Setup complete. Starting interview...")

#### Chat Bot Setup ####
# Here we check for 3 conditions to determine the next phase of app flow
if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:

    st.info(
        """
        Start by introducing yourself. 
        """,
        icon = "👋"
    )

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    # Setting up our model via sessions_state to check if the session state contains a variable for the model
    # If the session_state doesn't contain a variable we create one and assign it to "gpt-4o"
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = "gpt-4o"

    # Checks if the messages list is empty, which equals false and the not statement turns it true, allowing the code to initialize system message,
    # and dynamically insert the user provided data into the prompt message via the st.session_state.messages var
    if not st.session_state.messages:
        st.session_state.messages = [{
            "role": "system",
            "content": (f"Your are an HR executive that interviews an interviewee called {st.session_state["name"]} "
                        f"with experience {st.session_state["experience"]} and skills {st.session_state["skills"]}. "
                        f"You should interview them for the position {st.session_state["level"]} {st.session_state["position"]} "
                        f"at the company {st.session_state["company"]}")
        }]

    # This loop goes over each state message. If the role of the message is not system, we create a block that can take one of two roles, assistant or user.
    # Using markdown we put the content of the message. The loop goes through all messages and displays them.
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Here we limit the amount of responses so that the interview doesn't keep going indefinently. 
    if st.session_state.user_message_count < 5:   
        # The if prompt := syntax is a compact way to assign the value of the input to the prompt object and check if the input is not empty
        # Once we have input we append it to session_state.messages
        if prompt := st.chat_input("Your answer.", max_chars = 1000):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

        # Chat message block the assistant's repsonse and call the openai api to generate a response
        # First we use the with statement to create a context block.
        # Followed by the chat message method where we pass the assistant string as an argument to create a dedicated block to display response in the interface
        # Next, we call openai to generate response via the create method. The messages argument takes the entire chat history as context for response.
        # To provide context we loop through the session's messages list using list comprehension, iterating over existing one
        # In this case, extracts content role from each m in the list, and reformats it as a dictionary
        # Finally we capture the respones in a variable and append to the messages list
            # Assistant's response
            if st.session_state.user_message_count < 4:
                with st.chat_message("assistant"):
                    stream = client.chat.completions.create(
                        model=st.session_state["openai_model"],
                        messages=[
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages
                        ],
                        stream=True, # This line enables streaming for real-time response
                    )
                    # Display the assistant's response as it streams
                    response = st.write_stream(stream)
                # Append the assistant's full response to the 'messages' list
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            st.session_state.user_message_count += 1
    
    if st.session_state.user_message_count >= 5:
        st.session_state.chat_complete = True

#### Setup for interviewee feedback model ####
if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Get Feedback", on_click = show_feedback):
        st.write("Fetching feedback...")

if st.session_state.feedback_shown:
    st.subheader("Feedback")

    #Statement to create a chat history var which joins all state messages into a single string
    conversation_history = "\n".join([f"{msg["role"]}: {msg["content"]}" for msg in st.session_state.messages])

    # New model for evaluation
    feedback_client = OpenAI(api_key = st.secrets["OPENAI_API_KEY"])
    feedback_completion = feedback_client.chat.completions.create(
        model = "gpt-4o",
        messages = [
            {"role": "system", "content": """You are a helpful tool that provides feedback on an interviewee performance.
             Before the Feedback give a score of 1 to 10.
             Follow this format:
             Overall Score; //Your score
             Feedback: //Here you put your feedback
             Give only the feedback do not ask any additional questions.
             """},
             {"role": "user", "content": F"This is the interview you need to evaluate. Keep in mind that you are only a tool, and shouldn't engage in conversaton: {conversation_history}"}
        ]
    )

    # Here we extract the first message generated by the model. This is nessecary because the output of the feedback_completion function
    # is a structured object containing a list of potential responses, referred to as choices. 
    # Each item in the choices list represents a possible reply from the model, so we extract the first message from content which should be the feedback.  
    st.write(feedback_completion.choices[0].message.content)

    # Using java we implement a button that allows user to reset the interview from the beginning
    if st.button("Restart Interview", type = "primary"):
        streamlit_js_eval(js_expressions = "parent.window.locaiton.reload()")