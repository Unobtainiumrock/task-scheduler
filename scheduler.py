import os
import json
from openai import OpenAI, OpenAIError
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Initialize the OpenAI client
try:
    client = OpenAI()
except OpenAIError as e:
    print(f"Error initializing OpenAI client: {e}")
    print("Please make sure your OPENAI_API_KEY is set correctly in your .env file.")
    exit()

def create_timeline(user_input_text: str) -> dict:
    """
    Converts unstructured user text into a structured JSON timeline using an LLM.
    """
    
    # Get the current date and time to pass to the model
    now = datetime.now()
    current_date = now.strftime('%Y-%m-%d')
    current_time = now.strftime('%H:%M')

    # This is a refined "zero-shot" prompt. It gives clearer, more dynamic instructions
    # instead of a static example, which makes it more robust.
    system_prompt = f"""
    You are an expert scheduling assistant. Your task is to convert a user's unstructured to-do list into a structured JSON timeline.

    **Current Context:**
    - Today's Date: {current_date}
    - Current Time: {current_time}

    **Your Instructions:**
    1.  **Analyze and Prioritize**: Scrutinize the user's entire input to identify the highest-priority tasks that must be done *today*. Priority is determined by the closest deadlines (e.g., "due tomorrow" is higher priority than "due next week") and explicit user commands (e.g., "do this today").
    2.  **Build a Logical Schedule**: Create a realistic schedule for the rest of the day, starting from the **Current Time** ({current_time}).
    3.  **Structure Time Blocks**: Allocate focused work blocks (typically 60-90 minutes) for demanding tasks and shorter blocks for minor ones. Intelligently place short breaks (15 mins) between tasks and at least one longer break (e.g., for dinner).
    4.  **Enrich Task Names**: Make the `task_name` in the JSON descriptive. If a task has a deadline, mention it (e.g., "Work on Presentation (Due Sep 26th)").
    5.  **Strict JSON Output**: Your final output MUST be a valid JSON object and nothing else. Do not include any explanatory text, markdown, or comments.
    
    **JSON Output Schema:**
    {{
      "schedule_date": "YYYY-MM-DD",
      "tasks": [
        {{
          "task_name": "Descriptive name of the task",
          "start_time": "HH:MM",
          "end_time": "HH:MM",
          "duration_minutes": integer
        }}
      ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Using a more powerful model can improve reasoning
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input_text}
            ]
        )
        
        schedule_json = json.loads(response.choices[0].message.content)
        return schedule_json

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# --- HOW TO USE IT ---
if __name__ == "__main__":
    new_tasks_text = """
    # Tasks List
    
    - [ ] Meet Tianyi tonight from 9:00pm to 9:20pm
    
    ## Linear Regression 
    - [ ] Multicollinearity Exercise, due Sep 25th
    - [ ] Linear Regression HW 4, due Sep 28
    - [ ] HW5, due oct 5th
    - [ ] Exam 2 Oct 7th
    - [ ] Final Projcet, due Oct 10th

    ## Communication
    - [ ] Presentation, due Sep 26th
    - [ ] 

    ## Databases
    - [ ] HW Assignment, due Oct 3rd
    - [ ] Final Exam October 8th
    - [ ] 

    ## Data Acquisition

    ## Exam Prep
    - [ ] Go over my mistakes from the SQL exam
    - [ ] Watch all of Mahesh's recordings at x2 speed
    - [ ] Do Cody's practice exam, look over it today!

    ## Note Consolidation
    - [ ] Consolidate and refine notes on F-statistics from the class on Monday Sep 22nd
    - [ ] Consolidate data acquisition notes on docker compose and microservices for GCP. Where are these?
    - [ ] 

    ## Misc
    - [ ] Fill a forward of address form before moving!
    - [ ] Revisit the data I was working on from Emmett.
      - [ ] Finalize the system
      - [ ] Draft a technical blog post on my process and findings
    - [ ] Go over the OREOS for Lexis Nexis. What is this? Some kind of acronym?
    - [ ] Consolidate and refine notes on F-statistics from the class on Monday Sep 22nd
    - [ ] Add the reminder about the startup resources that Shan shared with me
    - [ ] Take apart laptop and get all the old hard drive material (windows surface)
    - [ ] Imporve the UI/UX in chat apps by making it possible to drag and drop lots of other conversations from the side bar as context to be used in a newly instantiated chat session
    - [ ] Add SVD v.s. Graph RAG chat to my project's scope. Go search for this in Gemini
    - [ ] Look up John Zerka
    - [ ] ROUGE is about content/completeness, BLEU is about correctness. Review this in my Gemini chat.

    ## Random Thoughts

    - [ ] What if each project had a chat space where it contains a history of all past Cursor chat or conversations had about the project being solved? See if this can be incorporated into my chat system.

    """

    print("Generating timeline for new tasks...")
    timeline = create_timeline(new_tasks_text)
    
    if timeline:
        # Pretty-print the JSON to the console
        print("--- Generated Schedule ---")
        print(json.dumps(timeline, indent=2))
        
        # *** NEW: Save the output to a file ***
        output_filename = "schedule.json"
        with open(output_filename, 'w') as f:
            json.dump(timeline, f, indent=2)
        print(f"\n✅ Schedule successfully saved to '{output_filename}'")

