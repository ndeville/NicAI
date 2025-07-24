250722-1749 TRANSFERED FROM OPENAEE - NEEDS TO BE UPDATED

from datetime import datetime
import os
ts_db = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
ts_time = f"{datetime.now().strftime('%H:%M:%S')}"
print(f"\n---------- {ts_time} starting {os.path.basename(__file__)}")
import time
start_time = time.time()

from dotenv import load_dotenv
load_dotenv()
DB_BTOB = os.getenv("DB_BTOB")
# DB_MAILINGEE = os.getenv("DB_MAILINGEE")

import pprint
pp = pprint.PrettyPrinter(indent=4)

####################
# NIC_KAL_MEETING_FU via API / Generate Meeting follow-up email

"""
Generate Meeting follow-up email, using transcript of meeting and account notes.
"""


# GLOBALS

import time
# import tiktoken
import json
# import sqlite3
# import my_utils
import subprocess


# from openaee_linkedin_profile import linkedin_profile_data_with_openai_from
# from extract_profile_data import linkedin_html_to_md/Users/nic/sh/nickal_meeting_fu.sh
# from DB.tools import select_all_records, update_record, create_record, delete_record

from generate_captions import generate_en_srt
# from openaee_update_system_prompts import update_assistant_prompts
from openaee_responses_api import generate_response

from openai import OpenAI
client = OpenAI()

# import json

# ASSISTANT_ID = os.getenv("NIC_KAL_MEETING_FU")

# update_assistant_prompts("NIC_KAL_MEETING_FU")

test = 1
verbose = 0

# FUNCTIONS

# def wait_on_run(run, thread):
#     while run.status == "queued" or run.status == "in_progress":
#         run = client.beta.threads.runs.retrieve(
#             thread_id=thread.id,
#             run_id=run.id,
#         )
#         time.sleep(0.5)
#     return run



# def generate_meeting_fu(specific_prompt, meeting_transcript, account_notes):
#     # Create a new JSON object with all required fields
#     user_prompt = json.dumps({
#         "specific_prompt": specific_prompt,
#         "meeting_transcript": meeting_transcript,
#         "account_notes": account_notes
#     }, indent=2)

#     if verbose:
#         print(f"\n\nℹ️  openaee_nickal_meeting_fu.py > user_prompt:\n{user_prompt}\n\n")

#     thread = client.beta.threads.create()

#     message = client.beta.threads.messages.create(
#         thread_id=thread.id,
#         role="user",
#         content=user_prompt,
#     )

#     run = client.beta.threads.runs.create(
#         thread_id=thread.id,
#         assistant_id=ASSISTANT_ID,
#     )

#     run = wait_on_run(run, thread)

#     messages = client.beta.threads.messages.list(thread_id=thread.id)

#     if verbose:
#         print("\n\nRun status:", run.status)

#     if run.status == "completed":
#         if verbose:
#             print(f"\n\nmessage:\n{messages}\n\n")
#         message_content = messages.data[0].content[0].text.value

#         if verbose:
#             print("\n\nRaw message content:\n")
#             print(message_content)

#         return message_content
    
#     else:
#         print(f"\n❌ Error: run not completed")
#         return False


def generate_meeting_fu(specific_prompt, meeting_transcript, account_notes):

    # system_prompt = ""
    with open("/Users/nic/Dropbox/Notes/kaltura/prompts/NicKalMeetingFU.md", 'r') as file:
        system_prompt = file.read()

    user_prompt = json.dumps({
        "specific_prompt": specific_prompt,
        "meeting_transcript": meeting_transcript,
        "account_notes": account_notes
    }, indent=2)

    print(f"\n\nℹ️  openaee_nickal_meeting_fu.py > user_prompt:\n{user_prompt}\n\n")

    return generate_response(system_prompt, user_prompt)




def append_email_to_notes(account_notes_path, meeting_fu_email):
    # Read the existing account notes
    with open(account_notes_path, 'r') as file:
        account_notes = file.read()
    
    # Append the meeting follow-up email
    account_notes += f"\n\n{meeting_fu_email}"

    # Save the updated account notes
    with open(account_notes_path, 'w') as file:
        file.write(account_notes)
    
    print(f"\n✅ Meeting follow-up email appended to account notes: {account_notes_path}")

    # Open the account notes in the default text editor
    subprocess.run(['open', account_notes_path])



########################################################################################################

if __name__ == '__main__':

    """
    TODO
    checks if the clipboard contains a file path to the video folder; otherwise, it takes the last modified video file in the video folder.
3. If a transcript of the video does not exist as a `.txt` file:
	* Run through the transcription process first.
4. Pass the transcript to the meeting follow-up assistant, which then generates an email follow-up.
5. Append the email follow-up in the account notes using markdown with a clear flag to send.
    """


    # Get clipboard content using subprocess
    clipboard_content = subprocess.check_output(['pbpaste']).decode('utf-8')

    video_file_path = None
    if clipboard_content and (clipboard_content.startswith("/Users/nic/vid") or clipboard_content.startswith("/Users/nic/aud")):
        if os.path.exists(clipboard_content):
            video_file_path = clipboard_content
            print(f"Using path from clipboard:\t{video_file_path}")
        else:
            print(f"Clipboard path does not exist: {clipboard_content}")
    
    # If no valid path from clipboard, get the last modified .mp4 file in the folder
    if not video_file_path:
        video_folder = "/Users/nic/vid"
        if os.path.exists(video_folder):
            mp4_files = [os.path.join(video_folder, f) for f in os.listdir(video_folder) if f.endswith('.mp4') and '-KA' in f]
            if mp4_files:
                video_file_path = max(mp4_files, key=os.path.getmtime)
                print(f"Using last modified video file:\t{video_file_path}")
            else:
                print(f"No .mp4 files found in {video_folder}")
        else:
            print(f"Video folder does not exist: {video_folder}")

    # # If a video file path is found, proceed with further processing
    # if video_file_path:
    #     # Placeholder for further processing like transcription and generating follow-up email
    #     print(f"Ready to process video file:\t{video_file_path}")
    # else:
    #     print("No video file to process.")


    # Check if a transcript (.txt) file already exists for the video
    transcript_file_path = os.path.splitext(video_file_path)[0] + ".txt"
    if os.path.exists(transcript_file_path):
        print(f"Transcript already exists:\t{transcript_file_path}")
    else:
        print(f"No transcript found for {video_file_path}. Transcription needed.")
        # Placeholder for transcription process
        print("Transcription process will be implemented here.")
        generate_en_srt(video_file_path)

        # Check if the transcript (.txt) file now exists after transcription
        if os.path.exists(transcript_file_path):
            print(f"Transcript successfully created: {transcript_file_path}")
        else:
            print(f"Transcript creation failed: {transcript_file_path}")

    with open(transcript_file_path, 'r') as file:
        transcript = file.read()

    # Extract account slug from the video file name
    file_name = os.path.basename(video_file_path)
    # account_slug = ""
    # try:
    #     if "-KA" in file_name:
    #         parts = file_name.split("-KA")
    #         if len(parts) > 1:
    #             slug_part = parts[1].strip().split(" ")[0]
    #             account_slug = slug_part.lower()
    #             print(f"Extracted account slug:\t\t{account_slug}")
    #         else:
    #             print("Could not extract account slug: format after '-KA' not as expected.")
    #     else:
    #         print("Could not extract account slug: '-KA' not found in filename.")
    #         account_slug = input("\nEnter account slug to fetch note > ")
    # except Exception as e:
    #     print(f"Error extracting account slug: {str(e)}")
    #     account_slug = input("\nEnter account slug to fetch note > ")
    
    account_slug = input("\nEnter account slug to fetch note > ")

    # Check for account notes file in clients or partners directory
    client_notes_path = f"/Users/nic/Dropbox/Notes/kaltura/clients/{account_slug}.md"
    partner_notes_path = f"/Users/nic/Dropbox/Notes/kaltura/partners/{account_slug}.md"
    account_notes_path = ""
    if os.path.exists(client_notes_path):
        account_notes_path = client_notes_path
        print(f"✅ Account notes found in clients: {account_notes_path}")
    elif os.path.exists(partner_notes_path):
        account_notes_path = partner_notes_path
        print(f"✅ Notes found in partners: {account_notes_path}")
    else:
        print(f"❌ No account notes found for slug: {account_slug}")

    # Read the account notes
    with open(account_notes_path, 'r') as file:
        account_notes = file.read()

    # Ask for specific prompt
    specific_prompt = input("\nEnter a specific prompt for the meeting follow-up email (or press Enter to use default): ")
    if not specific_prompt:
        specific_prompt = "ℹ️  No specific prompt provided. Generate a meeting follow-up email based on the meeting transcript and account notes as per your instructions."

    # Generate the meeting follow-up email
    print(f"\nGenerating meeting follow-up email...")

    if verbose:
        print(f"\n\nℹ️  openaee_nickal_meeting_fu.py > specific_prompt:\n{specific_prompt}\n\n")
        print(f"\n\nℹ️  openaee_nickal_meeting_fu.py > transcript:\n{transcript}\n\n")
        print(f"\n\nℹ️  openaee_nickal_meeting_fu.py > account_notes:\n{account_notes}\n\n")

    meeting_fu_email = generate_meeting_fu(specific_prompt, transcript, account_notes)
    if verbose:
        print(f"\n\nℹ️  openaee_nickal_meeting_fu.py > meeting_fu_email:\n{meeting_fu_email}\n\n")

    if "# Meeting Follow-up Email" in meeting_fu_email:
        meeting_fu_email = meeting_fu_email.replace("# Meeting Follow-up Email", "")

    # Append the email follow-up in the account notes using markdown with a clear flag to send
    append_email_to_notes(account_notes_path, meeting_fu_email)




    run_time = round((time.time() - start_time), 3)
    if run_time < 1:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time*1000)}ms at {datetime.now().strftime("%H:%M:%S")}.\n')
    elif run_time < 60:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time)}s at {datetime.now().strftime("%H:%M:%S")}.\n')
    elif run_time < 3600:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time/60)}mns at {datetime.now().strftime("%H:%M:%S")}.\n')
    else:
        print(f'\n{os.path.basename(__file__)} finished in {round(run_time/3600, 2)}hrs at {datetime.now().strftime("%H:%M:%S")}.\n')