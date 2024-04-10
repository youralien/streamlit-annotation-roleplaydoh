import streamlit as st
import json
from data_utils import *
import os

BUCKET_NAME = st.secrets.filenames["bucket_name"]
STATE = st.secrets.filenames["state_file"]
EXAMPLES = st.secrets.filenames["example_file"]

def update_global_dict(keys, dump = False):
    for key in keys:
        global_dict[key] = st.session_state[key]

    if not dump:
        return

    if "logged_in" in st.session_state and st.session_state["logged_in"]:
        # json.dump(global_dict, open(f"data/state_{st.session_state['logged_in']}.json", 'w'))
        save_dict_to_gcs(BUCKET_NAME, f"data/{STATE}_{st.session_state['logged_in']}.json", global_dict)
    elif "pid" in st.session_state and st.session_state["pid"]:
        client = get_gc_client()
        bucket = client.get_bucket(BUCKET_NAME)
        if storage.Blob(bucket=bucket, name=f"data/{STATE}_{st.session_state['pid']}.json").exists(client):
        # if os.path.exists(f"data/state_{st.session_state['pid']}.json"):
            # load
            return
        else:
            # json.dump(global_dict, open(f"data/state_{st.session_state['pid']}.json", 'w'))
             save_dict_to_gcs(BUCKET_NAME, f"data/{STATE}_{st.session_state['pid']}.json", global_dict)
    else:
        save_dict_to_gcs(BUCKET_NAME, f"data/{STATE}.json", global_dict)
        # json.dump(global_dict, open(f'data/state.json', 'w'))

def example_finished_callback():
    for _ in st.session_state:
        global_dict[_] = st.session_state[_]
    global_dict["current_example_ind"] += 1
    if "logged_in" in st.session_state and st.session_state["logged_in"]:
        save_dict_to_gcs(BUCKET_NAME, f"data/{STATE}_{st.session_state['logged_in']}.json", global_dict)
        # json.dump(dict(global_dict), open(f"data/state_{st.session_state['logged_in']}.json", 'w'))
    else:
        save_dict_to_gcs(BUCKET_NAME, f"data/{STATE}.json", global_dict)
        # json.dump(dict(global_dict), open(f'data/state.json', 'w'))
    js = '''
    <script>
        function scrollToTop() {
            var body = window.parent.document.querySelector(".main");
            body.scrollTop = 0;
        }
        setTimeout(scrollToTop, 300);  // 300 milliseconds delay
    </script>
    '''
    st.components.v1.html(js)



def get_id():
    """Document Prolific ID"""

    if "logged_in" in st.session_state and st.session_state["logged_in"]:
        return True

    col1, col2, col3 = st.columns([2,3,2])
    with col2:
        if "pid" in st.session_state and st.session_state["pid"]:
            st.session_state["logged_in"] = st.session_state["pid"]
            st.session_state["reload"] = True
            return True
        else:
            st.markdown(f'### A Conversational Tool for Training Peer Counselors')
            st.warning("""Before you log in and begin annotating data,
                        please ensure you have read and fully understood our research information sheet.
                        :red[**By providing your Email ID, you are providing your informed consent**] to participate in this research project.
                        If you have any questions or concerns about the research or your role in it,
                        please reach out to our team before proceeding.""", icon="⚠️")
            st.text_input("Email ID", key="pid", on_change=update_global_dict, args=[["pid"], "True"])
            st.session_state["reload"] = True
            return False


if __name__ == "__main__":

    st.set_page_config(layout="wide")

    if "reload" not in st.session_state or st.session_state["reload"]:
        if "logged_in" in st.session_state and st.session_state["logged_in"]:
            global_dict = read_or_create_json_from_gcs(BUCKET_NAME, f"data/{STATE}_{st.session_state['logged_in']}.json")
            # global_dict = json.load(open(f"data/state_{st.session_state['logged_in']}.json", 'r'))
        elif "pid" in st.session_state and st.session_state["pid"]:
            global_dict = read_or_create_json_from_gcs(BUCKET_NAME, f"data/{STATE}_{st.session_state['pid']}.json")
            # global_dict = json.load(open(f"data/state_{st.session_state['pid']}.json", 'r'))
        else:
            global_dict = read_or_create_json_from_gcs(BUCKET_NAME, f"data/{STATE}.json")
            # global_dict = json.load(open(f'data/state.json', 'r'))
        st.session_state["reload"] = False
        st.session_state["testcases"] = global_dict["testcases"]
        st.session_state["current_example_ind"] = global_dict["current_example_ind"]
    else:
        global_dict = st.session_state

    if "testcases_text" not in st.session_state:
        testcases = read_or_create_json_from_gcs(BUCKET_NAME, f"data/{EXAMPLES}.json")
        # testcases = json.load(open('data/errors_test.json', 'r'))
        st.session_state["testcases_text"] = testcases

    testcases = st.session_state["testcases_text"]

    if get_id():

        example_ind = global_dict["current_example_ind"]

        with st.sidebar:
            st.markdown(""" # **Annotation Instructions**

- You have been provided a conversation between a simulated patient and a therapist, along with a description of the patient's situation and personality, and a set of principles that the patient response should follow.
- Rank the patient responses shown based on the set of dimensions provided. A lower rank indicates a better response!
- The same rank can be assigned to multiple responses, if required. For example, if the first and second response are of similar quality, and both are better than the third response, rank 1 should be assigned to the first two responses, and rank 2 should be assigned to the third response.

""")

        c1, c2, c3 = st.columns([1,5,1])
        with c2:
            if example_ind >= len(global_dict["testcases"]):
                st.title("Thank you!")
                st.balloons()
                st.success("You have annotated all the examples! 🎉")

            else:

                for key in global_dict:
                    st.session_state[key] = global_dict[key]

                st.markdown(f'### **Response Annotation for Roleplaydoh**')
                st.info("This is a tool to rank patient responses generated from different models along different dimensions. Please read the conversation, patient description and set of principles for the patient to follow below and provide responses in the following sections.")
                st.subheader(f"Case {example_ind + 1} of {len(global_dict['testcases'])}")
                example_ind = global_dict["current_example_ind"]
                testcase = testcases["tests"][global_dict["testcases"][example_ind]]

                count_required_feedback = 0
                count_done_feedback = 0

                with st.container():
                    st.markdown(f'### **Description of Patient**')
                    st.markdown(testcase["input"]["description"])

                    conv = testcase["input"]["messages"]
                    st.markdown(f'### **Conversation History**')
                    for i in range(len(conv)):
                        to_print = f"**{conv[i]['role']}** : {conv[i]['content']}"
                        if conv[i]["role"] == 'therapist':
                            st.markdown(f':blue[{to_print}]')
                        else:
                            st.markdown(f':red[{to_print}]')

                    # principles_list = f'### **Principles**'
                    # for _ in testcase["input"]["principles"]:
                    #     principles_list += f'\n- {_}'
                    # st.markdown(principles_list)

                responses = testcase["responses"]
                with st.container():
                    st.markdown(f'### **Dimension 1**')
                    st.markdown('Rank responses based on how consistent they are to the patient description and conversation history, and if they offer an appropriate reply to the last message from the therapist. All suitably consistent responses should have the same rank.')

                    for idx, response in enumerate(responses):
                        col1, col2 = st.columns([4,2])
                        with col1:
                            to_print = f"**patient** : {response['message']}"
                            st.markdown(f':red[{to_print}]')
                            count_required_feedback += 1

                        with col2:
                            key = f'{example_ind}_1_{idx}'
                            st.selectbox(label="Rank", options=["None"] + [str(_+1) for _ in list(range(len(responses)))], on_change = update_global_dict, args=[[key]], key=key)
                            if key in st.session_state and st.session_state[key] != "None":
                                count_done_feedback += 1

                with st.container():
                    st.markdown(f'### **Dimension 2**')
                    # st.markdown('The response avoids stylistic errors. Such errors may include: starting a sentence with a greeting in the middle of a conversation, or always ending a response with an abbreviation.')
                    st.markdown('Evaluate whether each response has an awkward style of speech. An example of awkward style could be starting a sentence with a greeting in the middle of a conversation.')

                    for idx, response in enumerate(responses):
                        col1, col2 = st.columns([4,2])
                        with col1:
                            to_print = f"**patient** : {response['message']}"
                            st.markdown(f':red[{to_print}]')
                            count_required_feedback += 1

                        with col2:
                            key = f'{example_ind}_2_{idx}'
                            st.selectbox(label="Is this response awkward?", options=["None", "Yes", "No"], on_change = update_global_dict, args=[[key]], key=key)
                            if key in st.session_state and st.session_state[key] != "None":
                                count_done_feedback += 1

                with st.container():
                    st.markdown(f'### **Dimension 3**')
                    st.markdown('Rank responses based on how well they adhere to all the written principles. If a response violates a principle, the extent to which the principle is violated should not be taken into account while ranking. Models which violate fewer number of principles should be ranked higher.')

                    principles_list = f'##### **Principles for Patient Actor to Follow**'
                    for _ in testcase["input"]["principles"]:
                        principles_list += f'\n- {_}'
                    st.markdown(principles_list)

                    for idx, response in enumerate(responses):
                        col1, col2 = st.columns([4,2])
                        with col1:
                            to_print = f"**patient** : {response['message']}"
                            st.markdown(f':red[{to_print}]')
                            count_required_feedback += 1

                        with col2:
                            key = f'{example_ind}_3_{idx}'
                            st.selectbox(label="Rank", options=["None"] + [str(_+1) for _ in list(range(len(responses)))], on_change = update_global_dict, args=[[key]], key=key)
                            if key in st.session_state and st.session_state[key] != "None":
                                count_done_feedback += 1

                with st.container():
                    st.markdown(f'### **Overall Ranking**')
                    st.markdown('Based on your answers for the dimensions above, provide an overall ranking for the responses in the context of the patient description, conversation history and set of principles. In cases where responses do not have significant errors according to dimensions 1 and 2, the overall ranking can be determined on the basis of dimension 3.')

                    for idx, response in enumerate(responses):
                        col1, col2 = st.columns([4,2])
                        with col1:
                            to_print = f"**patient** : {response['message']}"
                            st.markdown(f':red[{to_print}]')
                            count_required_feedback += 1

                        with col2:
                            key = f'{example_ind}_4_{idx}'
                            st.selectbox(label="Rank", options=["None"] + [str(_+1) for _ in list(range(len(responses)))], on_change = update_global_dict, args=[[key]], key=key)
                            if key in st.session_state and st.session_state[key] != "None":
                                count_done_feedback += 1
                            
                    count_required_feedback += 1
                    st.text_area("Please provide a brief explanation for the overall ranking provided above.", key=f"reason_{example_ind}", on_change=update_global_dict, args=[[f"reason_{example_ind}"]], height=200)
                    if f"reason_{example_ind}" in st.session_state and st.session_state[f"reason_{example_ind}"]:
                        count_done_feedback += 1

                st.checkbox('I have finished annotating', key=f"finished_{example_ind}", on_change=update_global_dict, args=[[f"finished_{example_ind}"]])

                if f"finished_{example_ind}" in st.session_state and st.session_state[f"finished_{example_ind}"]:
                    if count_done_feedback != count_required_feedback:
                        st.error('Some annotations seem to be missing. Please annotate the full conversation', icon="❌")
                    else:
                        st.success('We got your annotations!', icon="✅")
                        st.button("Submit final answers and go to next testcase", type="primary", on_click=example_finished_callback)
                        st.session_state["reload"] = True
