
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, ChatMessage

# --------------------------------------------------------------
# Load Gemini API Token From the .env File
# --------------------------------------------------------------
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")

# --------------------------------------------------------------
# LinkedIn Content Creation Function Descriptions
# --------------------------------------------------------------
function_descriptions = [
    {
        "name": "prompt_for_ideas",
        "description": "Prompt the user to submit new LinkedIn content ideas. Returns a list of ideas.",
        "parameters": {
            "type": "object",
            "properties": {
                "ideas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of LinkedIn content ideas to refine and prioritize."
                }
            },
            "required": ["ideas"]
        },
    },
    {
        "name": "manage_brainstorming_session",
        "description": "Facilitate a brainstorming session, allowing the user to expand, refine, and prioritize ideas. Returns a list of refined and prioritized ideas.",
        "parameters": {
            "type": "object",
            "properties": {
                "ideas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of LinkedIn content ideas to refine and prioritize."
                }
            },
            "required": ["ideas"]
        },
    },
    {
        "name": "co_write_post",
        "description": "Co-write a LinkedIn post based on the selected idea. Optionally uses an LLM for suggestions. Returns the drafted post.",
        "parameters": {
            "type": "object",
            "properties": {
                "idea": {
                    "type": "string",
                    "description": "The LinkedIn content idea to turn into a post."
                },
                "llm": {
                    "type": "string",
                    "description": "Optional. The language model to use for suggestions."
                }
            },
            "required": ["idea"]
        },
    },
    {
        "name": "finalize_and_track_post",
        "description": "Mark a post as finalized and track it in a local file.",
        "parameters": {
            "type": "object",
            "properties": {
                "post": {
                    "type": "string",
                    "description": "The finalized LinkedIn post content."
                },
                "tracking_file": {
                    "type": "string",
                    "description": "Optional. The file to track finalized posts. Default is 'linkedin_posts.json'."
                }
            },
            "required": ["post"]
        },
    },
    {
        "name": "daily_reminder",
        "description": "Remind the user daily to create or finalize LinkedIn content.",
        "parameters": {
            "type": "object",
            "properties": {
                "reminder": {
                    "type": "datetime",
                    "description": "The date and time of the reminder."
                }
            },
            "required": ["reminder"]
        },
    },
]

# --------------------------------------------------------------
# LinkedIn Content Creation Helper Functions
# --------------------------------------------------------------
import datetime
import json as _json
import os as _os

def prompt_for_ideas():
    """
    Prompt the user to submit new LinkedIn content ideas.
    Returns a list of ideas.
    """
    ideas = []
    print("Let's brainstorm LinkedIn content ideas!")
    while True:
        idea = input("Enter a content idea (or type 'done' to finish): ")
        if idea.strip().lower() == 'done':
            break
        ideas.append(idea)
    return ideas

def manage_brainstorming_session(ideas):
    """
    Facilitate a brainstorming session, allowing the user to expand, refine, and prioritize ideas.
    Returns a list of refined and prioritized ideas.
    """
    print("\nLet's refine and prioritize your ideas.")
    refined_ideas = []
    for i, idea in enumerate(ideas, 1):
        print(f"\nIdea {i}: {idea}")
        refined = input("Refine or expand this idea (or press Enter to keep as is): ")
        if refined.strip():
            refined_ideas.append(refined)
        else:
            refined_ideas.append(idea)
    # Prioritize
    print("\nPrioritize your ideas (enter numbers in order, separated by commas):")
    for idx, idea in enumerate(refined_ideas, 1):
        print(f"{idx}: {idea}")
    order = input("Order: ")
    order_indices = [int(x.strip())-1 for x in order.split(',') if x.strip().isdigit() and 0 < int(x.strip()) <= len(refined_ideas)]
    prioritized_ideas = [refined_ideas[i] for i in order_indices]
    return prioritized_ideas

def co_write_post(idea, llm=None):
    """
    Co-write a LinkedIn post based on the selected idea.
    Optionally uses an LLM for suggestions.
    Returns the drafted post.
    """
    print(f"\nLet's write a post for: {idea}")
    draft = input("Write your draft (or press Enter to get AI help): ")
    if not draft and llm:
        # Use LLM to generate a draft
        draft = llm.generate_linkedin_post(idea)
        print(f"AI Draft: {draft}")
        edit = input("Edit the draft or press Enter to accept: ")
        if edit.strip():
            draft = edit
    return draft

def finalize_and_track_post(post, tracking_file='linkedin_posts.json'):
    """
    Mark a post as finalized and track it in a local file.
    """
    finalized = input("Is this post finalized and ready to publish? (y/n): ")
    if finalized.strip().lower() == 'y':
        post_entry = {
            'content': post,
            'date_finalized': datetime.datetime.now().isoformat()
        }
        if _os.path.exists(tracking_file):
            with open(tracking_file, 'r') as f:
                posts = _json.load(f)
        else:
            posts = []
        posts.append(post_entry)
        with open(tracking_file, 'w') as f:
            _json.dump(posts, f, indent=2)
        print("Post finalized and tracked!")
    else:
        print("Post not finalized.")

def daily_reminder():
    """
    Remind the user daily to create or finalize LinkedIn content.
    (This is a placeholder; in production, use a scheduler like cron or APScheduler.)
    """
    print("🔔 Daily Reminder: Don't forget to create or finalize your LinkedIn post today!")

# --------------------------------------------------------------
# Interactive Functions
# --------------------------------------------------------------

def ask_and_reply(prompt):
    """Give Gemini a given prompt and get an answer."""
    response = model.generate_content(prompt)
    return response.text

def main():
    print("Welcome to the Flight Assistant! Type 'exit' to quit.")
    while True:
        user_prompt = input("\nWhat would you like to do? ")
        if user_prompt.strip().lower() == 'exit':
            print("Goodbye!")
            break
        # Get Gemini response
        output = ask_and_reply(user_prompt)
        print("\nGemini Response:")
        print(output)

if __name__ == "__main__":
    main()