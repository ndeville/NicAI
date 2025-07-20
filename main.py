from datetime import datetime
import os
import time
start_time = time.time()

# Load configurations from config.yaml
import yaml
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "config.yaml")
with open(config_path) as f:
    config = yaml.safe_load(f)

# Load my other modules
from openaee_responses_api import generate_response # Generate responses from OpenAI API
from extract_profile_data import linkedin_html_to_md # Extract LinkedIn profile data from HTML

verbose = True
if verbose:
    print(f"\nℹ️  Verbose mode ENABLED.")
else:
    print(f"\nℹ️  Verbose mode DISABLED.")

# 1 - GET THE USER PROMPT FROM THE LATEST TXT FILE IN THE TXT FOLDER

def get_latest_modified_txt_file():
    import os
    import glob

    directories = config.get('txt_directories')
    
    # Get list of all .txt files across all directories
    txt_files = []
    for directory in directories:
        if os.path.exists(directory):
            txt_files.extend(glob.glob(os.path.join(directory, "*.txt")))
    
    if not txt_files:
        return None
        
    # Find the most recently modified file across all directories
    latest_file = max(txt_files, key=os.path.getmtime)
    
    # Read and return the content of the latest file
    with open(latest_file, 'r', encoding='utf-8') as file:
        content = file.read()
    
    return latest_file, content

user_prompt_from_txt = get_latest_modified_txt_file()

print(f"\nℹ️  User prompt from txt file: {user_prompt_from_txt[0]}")

user_prompt = f"\n\n# TASK CONTEXT\n\n{user_prompt_from_txt[1]}"


# Pre-pend or append the user prompt with additional task-based context (eg. Linkedin profile data or specifying the account notes file)

## Linkedin profile data

def extract_linkedin_url(text):

    import re
    
    # Regular expression pattern for LinkedIn profile URLs
    linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/(?:in/|pub/|profile/)[a-zA-Z0-9-]+/?'
    
    # Search for the pattern in the text
    match = re.search(linkedin_pattern, text)
    
    if match:
        url = match.group(0)
        # Exclude URLs containing "ndeville"
        if "ndeville" not in url:
            return url
    return None

# Check if a LinkedIn URL is in the user prompt
linkedin_url = extract_linkedin_url(user_prompt)
if linkedin_url:
    print(f"LinkedIn profile URL found: {linkedin_url}")
    linkedin_md = linkedin_html_to_md(linkedin_url)
    # Increment headers in linkedin_md by 2 levels (e.g., # to ###)
    lines = linkedin_md.split('\n')
    modified_lines = []
    for line in lines:
        if line.startswith('#'):
            # Count the number of '#' characters at the start
            header_level = len(line.split(' ')[0])
            # Add two more '#' characters to increase the header level by 2
            new_header = '#' * (header_level + 2)
            # Replace the old header with the new one
            modified_line = new_header + line[header_level:]
            modified_lines.append(modified_line)
        else:
            modified_lines.append(line)
    linkedin_md = '\n'.join(modified_lines)
    print(f"\nℹ️  LinkedIn profile data:\n\n{linkedin_md}")
    user_prompt = f"{user_prompt}\n\n## Linkedin profile data\n\n{linkedin_md}"
else:
    print("\nℹ️  (TERMINAL ONLY) No LinkedIn profile URL found in the user prompt.")


## Account notes file

import re
from typing import List, Optional

def extract_emails(text: str):

    exclude_domains = config.get('exclude_domains')

    pattern = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
    emails = pattern.findall(text)

    filtered = []
    for email in emails:
        lower = email.lower()
        if not any(lower.endswith(domain.lower()) for domain in exclude_domains):
            filtered.append(lower)

    filtered.sort()

    return filtered

emails_found = extract_emails(user_prompt)

def get_dict_email_domains_to_account_note_file_path():
    """
    Scan a directory for .md files and extract email domains from each file, excluding @kaltura.com.
    Returns a dictionary mapping each email domain to the account slug path.
    Includes logic for exceptions where specific email domains always map to a predefined account slug.
    """
    import re
    import glob

    directory = os.getenv("KA_CLIENTS_NOTES")

    blacklist_domains = config.get('blacklist_domains')
    
    # Define exception domains and their corresponding account slugs
    exception_domains = config.get('exception_domains')
    
    md_files = glob.glob(f"{directory}/*.md")
    domain_to_file = {}
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b'
    
    for md_file in md_files:
        filename = os.path.basename(md_file)
        full_path = md_file
        
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                emails = re.findall(email_pattern, content)
                # Extract just the domain part and exclude kaltura.com
                for domain in emails:
                    domain_lower = domain.lower()
                    if domain_lower not in blacklist_domains:
                        # Check if domain is in exceptions; if so, use predefined slug
                        if domain_lower in exception_domains:
                            domain_to_file[domain_lower] = exception_domains[domain_lower]
                        else:
                            domain_to_file[domain_lower] = full_path.replace(directory, '').replace('.md', '').lstrip('/')
        except Exception as e:
            print(f"Error reading {filename}: {e}")

    # pp.pprint(domain_to_file)

    return domain_to_file

# Get the account slugs from the user prompt either via command or via emails
account_slugs = set()
update_with_account_context = False
# Try first to check if the user prompt contains an account slug (starting with a slash)
for line in user_prompt.split('\n'):
    if line.strip().startswith('/'):
        parts = line.split(' ', 1)
        if parts[0].startswith('/'):
            account_slug = parts[0][1:].strip()
            # if verbose:
            #     print(f"\nℹ️  Account slug extracted: {account_slug}")
            account_slugs.add(account_slug)
            break

if account_slugs and len(account_slugs) > 0:
    # if verbose:
    #     print(f"Account slugs found: {account_slug}")
    update_with_account_context = True
    
else:
# Else try to get the account_slugs from the emails_found
    # if emails_found and verbose:
    #     print(f"\nℹ️  Account emails found:")
    #     for pemail in emails_found:
    #         print(f"- {pemail}")
    unique_domains = set()
    for email in emails_found:
        if '@' in email:
            domain = email.split('@')[1]
            unique_domains.add(domain)
    unique_domains = list(unique_domains)
    if unique_domains:
        dict_email_domains_to_account_note_file_path = get_dict_email_domains_to_account_note_file_path()
        for domain in unique_domains:
            account_slug = dict_email_domains_to_account_note_file_path.get(domain)
            if account_slug:
                account_slugs.add(account_slug)
                update_with_account_context = True
    else:
        account_slugs = None

if verbose:
    if account_slugs and len(account_slugs) > 0:
        print(f"\nℹ️  {len(account_slugs)} account slug{'' if len(account_slugs) == 1 else 's'} found:")
        for aslug in account_slugs:
            print(f"- {aslug}")
    else:
        print("\nℹ️  (TERMINAL ONLY) No account slugs found in the user prompt.")

if update_with_account_context:
    # Prepare a list of file names for the context instruction
    file_names = "\n- ".join([slug for slug in account_slugs])
    user_prompt = f"""
# ACCOUNT CONTEXT

To find more context about the company/account this task is related to, use the **nicai_knowledge** vector store and use **Account-note files** (`content_type == "account_notes"`): include **only** those whose `file_name` appears in the list below; ignore all other account-note files to avoid cross-leakage and hallucinations.  

<file_name_attribute>
- {file_names}
</file_name_attribute>

**All other content types (ie files with other content_type attributes)**: include them without restriction.

{user_prompt}
"""

    # print(f"\n{user_prompt}")


# 2 - GET THE SYSTEM PROMPT FROM THE PROMPTS FOLDER

# Create a dictionary with integer keys and filenames as values for files in the specified folder
prompt_files_dict = {}
prompts_folder_path = "/Users/nic/Dropbox/Notes/ai/prompts"

# Check if the directory exists
if os.path.exists(prompts_folder_path):
    # Get all files in the directory
    all_files = [f for f in os.listdir(prompts_folder_path) if "_v" not in f and not f.startswith('__') and f.endswith('.md')]
    
    # Separate NicAI.md from other files
    nicai_file = None
    other_files = []
    
    for filename in all_files:
        if filename == 'NicAI.md':
            nicai_file = filename
        else:
            other_files.append(filename)
    
    # Sort other files alphabetically
    other_files.sort(key=str.lower)
    
    # Build the dictionary with NicAI.md as index 1
    index = 1
    if nicai_file:
        prompt_files_dict[index] = nicai_file
        index += 1
    
    for filename in other_files:
        prompt_files_dict[index] = filename
        index += 1

    # Print the dictionary for user reference
    print("\nAvailable system prompts:\n")
    for key, value in prompt_files_dict.items():
        print(f"{key}: {value.replace('.md', '')}")
else:
    print(f"Directory {prompts_folder_path} does not exist.")

print(f"\n(loaded in {round((time.time() - start_time)*1000)}ms)")

user_input = input("\n> Enter the code of the system prompt to use: ")


system_prompt = ""
selected_file = prompt_files_dict.get(int(user_input)) if user_input.isdigit() else None
if selected_file:
    file_path = os.path.join(prompts_folder_path, selected_file)
    if os.path.exists(file_path) and file_path.endswith('.md'):
        with open(file_path, 'r', encoding='utf-8') as file:
            system_prompt = file.read()
            
        # If selected file starts with "_", prepend NicAI.md content
        if selected_file.startswith('_'):
            nicai_path = os.path.join(prompts_folder_path, 'NicAI.md')
            if os.path.exists(nicai_path):
                with open(nicai_path, 'r', encoding='utf-8') as nicai_file:
                    system_prompt = nicai_file.read() + "\n\n# TASK CONTEXT\n\n" + system_prompt
                print(f"\nℹ️  Prepended NicAI.md to system prompt")
                    
        print(f"\nℹ️  Using system prompt from: {selected_file}")

        # Complement some system prompts
        if "Email" in selected_file: # add common output format for emails
            email_format_path = "/Users/nic/Dropbox/Notes/ai/prompts/__EmailFormat.md"
            with open(email_format_path, 'r', encoding='utf-8') as email_format_file:
                email_format_content = email_format_file.read()
                system_prompt += email_format_content
                print(f"    + email format instructions appended to system prompt")

    else:
        print(f"File {selected_file} is not a markdown file or does not exist.")
else:
    print(f"No system prompt found for input: {user_input}")






# 3 - GENERATE THE RESPONSE
query_start_time = time.time()
answer = generate_response(system_prompt, user_prompt, model="o3", filters=None, stream=True)
print(f"\nℹ️  query run time: {(lambda r: (f'{round(r*1000)}ms' if r<1 else f'{round(r)}s' if r<120 else f'{round(r/60)}mns' if r<3600 else f'{round(r/3600,2)}hrs'))(time.time()-query_start_time)} ")


# 4 - WRITE THE RESPONSE TO A TXT FILE

# Define the output directory for chat logs
output_dir = "/Users/nic/ai/chats"

# Ensure the output directory exists
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Generate a timestamp for the filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Create the output filename with timestamp
output_filename = f"chat_{timestamp}.txt"
output_path = os.path.join(output_dir, output_filename)

# Write the user prompt and the generated answer to the file
with open(output_path, 'w', encoding='utf-8') as f:
    f.write("<original_user_prompt>\n")
    f.write(user_prompt)
    f.write("\n</original_user_prompt>\n\n\n\n\n")
    f.write("<original_ai_response>\n\n")
    f.write(answer)
    f.write("\n\n</original_ai_response>\n")

print(f"\nℹ️  Chat log saved to: {output_path}")


# 5 - COPY THE ANSWER TO THE CLIPBOARD

# Copy the answer to the clipboard
import subprocess
process = subprocess.Popen("pbcopy", universal_newlines=True, stdin=subprocess.PIPE)
process.communicate(answer)

print(f"\n📝  Copied answer to clipboard: {answer}")



# 6 - ADD TO THE ACCOUNT NOTE FILE OR TEXT EDITOR

# Select the account slug to use to update the account note file
account_slug = None
if account_slugs and len(account_slugs) == 1:
    account_slug = list(account_slugs)[0]
elif account_slugs and len(account_slugs) > 1:
    for i, slug in enumerate(account_slugs, 1):
        print(f"  {i}. {slug}")
    while True:
        try:
            choice = int(input("\n> Enter the number of the account slug to use: "))
            if 1 <= choice <= len(account_slugs):
                account_slug = list(account_slugs)[choice - 1]
                break
            else:
                print(f"Please enter a number between 1 and {len(account_slugs)}.")
        except ValueError:
            print("Please enter a valid number.")


if account_slug:
    account_notes_dir = os.getenv("KA_CLIENTS_NOTES")
    if account_notes_dir:
        account_note_path = os.path.join(account_notes_dir, f"{account_slug}.md")
        if os.path.exists(account_note_path):
            try:
                # Append the AI response to the account note file
                with open(account_note_path, 'a', encoding='utf-8') as f:
                    f.write("\n\n\n")
                    f.write(answer)
                    f.write("\n\n---\n\n")
                print(f"\nℹ️  Appended AI response to account note for '{account_slug}' at: {account_note_path}")
                # Open the account note file in Cursor
                subprocess.run(['open', '-a', 'Cursor', account_note_path])
                print(f"\nℹ️  Opened account note for '{account_slug}' in Cursor: {account_note_path}")
            except Exception as e:
                print(f"❌ Error opening account note in Cursor: {str(e)}")
        else:
            print(f"❌ Account note file not found for '{account_slug}' at: {account_note_path}")
    else:
        print("❌ Environment variable 'KA_CLIENTS_NOTES' not set for account notes directory.")
else:
    print("\nℹ️  No account slug found in the user prompt. Skipping opening account notes, opening chat log .txt instead.")
    try:
        subprocess.run(['open', '-a', 'CotEditor', output_path])
        print(f"\nℹ️  Opened chat log in CotEditor: {output_filename}")
    except Exception as e:
        print(f"❌ Error opening chat log in CotEditor: {str(e)}")


print(
    f"\n{os.path.basename(__file__)} finished in "
    # f"{(lambda r: (f'{round(r*1000)}ms' if r<1 else f'{round(r)}s' if r<60 else f'{round(r/60)}mns' if r<3600 else f'{round(r/3600,2)}hrs'))(time.time()-start_time)} "
    f"{(lambda r: (f'{round(r*1000)}ms' if r<1 else f'{round(r)}s' if r<120 else f'{round(r/60)}mns' if r<3600 else f'{round(r/3600,2)}hrs'))(time.time()-start_time)} "
    f"at {datetime.now().strftime('%H:%M:%S')}.\n"
)