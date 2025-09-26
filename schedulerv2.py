import os
import json
import argparse  # NEW: Import the argparse library
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
    1.  **Define Working Hours**: The user's workday ends at **11:00 PM (23:00)**. You should schedule focused work blocks and necessary breaks up until this time. # NEW INSTRUCTION
    2.  **Analyze and Prioritize**: Scrutinize the user's entire input to identify the highest-priority tasks that must be done *today*. Priority is determined by the closest deadlines (e.g., "due tomorrow" is higher priority than "due next week") and explicit user commands (e.g., "do this today").
    3.  **Build a Logical Schedule**: Create a realistic schedule for the rest of the day, starting from the **Current Time** ({current_time}) and ending at **23:00**.
    4.  **Structure Time Blocks**: Allocate focused work blocks (typically 60-90 minutes) for demanding tasks and shorter blocks for minor ones. Intelligently place short breaks (15 mins) between tasks and at least one longer break (e.g., for dinner).
    5.  **Enrich Task Names**: Make the `task_name` in the JSON descriptive. If a task has a deadline, mention it (e.g., "Work on Presentation (Due Sep 26th)").
    6.  **Strict JSON Output**: Your final output MUST be a valid JSON object and nothing else. Do not include any explanatory text, markdown, or comments.

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
    parser = argparse.ArgumentParser(description="Generate a JSON schedule from a markdown file of tasks.")
    parser.add_argument("filename", help="The path to the markdown file containing the tasks.")
    args = parser.parse_args()

    try:
        with open(args.filename, 'r') as f:
            tasks_from_file = f.read()
    except FileNotFoundError:
        print(f"Error: The file '{args.filename}' was not found.")
        exit()
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        exit()

    print(f"Generating timeline from '{args.filename}'...")
    timeline = create_timeline(tasks_from_file)
    
    if timeline:
        # Pretty-print the JSON to the console
        print("--- Generated Schedule ---")
        print(json.dumps(timeline, indent=2))
        
        # Save the output to a file
        output_filename = "schedule.json"
        with open(output_filename, 'w') as f:
            json.dump(timeline, f, indent=2)
        print(f"\n✅ Schedule successfully saved to '{output_filename}'")
