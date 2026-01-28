import json
import requests
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import os
import httpx

# Load environment variables from .env file
load_dotenv()

# API and URL configurations from .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_API_URL = "https://api.notion.com/v1/pages"
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# Gemini API setup using OpenAI compatibility layer
client = OpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    http_client=httpx.Client()  # Fix for proxies error
)

# Global variable to store the latest post
latest_post = None

# Function definitions for Open AI-style function calling
FUNCTIONS = [
    {
        "name": "brainstorm_content",
        "description": "Generate answers to brainstorming questions for LinkedIn content.",
        "parameters": {
            "type": "object",
            "properties": {
                "idea": {"type": "string", "description": "The post idea"},
                "questions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of questions to spark ideas"
                }
            },
            "required": ["idea", "questions"]
        }
    },
    {
        "name": "co_write_post",
        "description": "Co-write a LinkedIn post with professional, thoughtful, and authentic tone.",
        "parameters": {
            "type": "object",
            "properties": {
                "draft": {"type": "string", "description": "Initial draft or idea"},
                "tone": {"type": "string", "description": "Desired tone"},
                "improvements": {"type": "string", "description": "Suggestions for structure, clarity, engagement"}
            },
            "required": ["draft"]
        }
    },
    {
        "name": "update_notion",
        "description": "Add or update a post in Notion under LinkedIn Content Calendar.",
        "parameters": {
            "type": "object",
            "properties": {
                "post_id": {"type": "string", "description": "Unique ID for the post"},
                "title": {"type": "string", "description": "Post title or summary"},
                "content": {"type": "string", "description": "Post content or notes"},
                "status": {
                    "type": "string",
                    "enum": ["Idea", "Draft", "Final", "Posted"],
                    "description": "Current status of the post"
                }
            },
            "required": ["post_id", "title", "content", "status"]
        }
    }
]

# Function implementations
def brainstorm_content(idea, questions):
    answers = []
    for question in questions:
        response = client.chat.completions.create(
            model="gemini-2.5-flash",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional LinkedIn ghostwriter hired to create engaging content. "
                        "Generate a concise (1-2 sentences), authentic, and professional answer to a brainstorming question for a LinkedIn post, "
                        "as if crafting content for a client's audience."
                    )
                },
                {"role": "user", "content": f"For the post idea '{idea}', answer this question: {question}"}
            ]
        )
        answers.append(response.choices[0].message.content)
    return {"answers": answers}

def co_write_post(draft, tone="professional, thoughtful, authentic", improvements=None):
    prompt = f"Write a LinkedIn post (150-280 characters) with a {tone} tone based on this draft: {draft}"
    if improvements:
        prompt += f"\nIncorporate these suggestions: {improvements}"
    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional LinkedIn ghostwriter hired to create engaging content. "
                    "Craft a concise (150-280 characters), engaging, and authentic LinkedIn post, "
                    "as if written by a human for a client's professional audience. Ensure it includes a call-to-action and relevant hashtags."
                )
            },
            {"role": "user", "content": prompt}
        ]
    )
    post_content = response.choices[0].message.content
    # Ensure post is within 150-280 characters
    if len(post_content) > 280:
        post_content = post_content[:277] + "..."
    elif len(post_content) < 150:
        post_content += " Share your thoughts! #LinkedIn"
    return {"revised_draft": post_content}

def update_notion(post_id, title, content, status):
    query_url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    query_data = {
        "filter": {
            "property": "Post ID",
            "rich_text": {"equals": post_id}
        }
    }
    response = requests.post(query_url, headers=NOTION_HEADERS, json=query_data)
    results = response.json().get("results", [])

    page_data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Post ID": {"rich_text": [{"text": {"content": post_id}}]},
            "Title": {"title": [{"text": {"content": title}}]},
            "Content": {"rich_text": [{"text": {"content": content}}]},
            "Status": {"select": {"name": status}},
            "Date": {"date": {"start": datetime.now().isoformat()}}
        }
    }

    if results:
        page_id = results[0]["id"]
        update_url = f"https://api.notion.com/v1/pages/{page_id}"
        response = requests.patch(update_url, headers=NOTION_HEADERS, json=page_data)
    else:
        response = requests.post(NOTION_API_URL, headers=NOTION_HEADERS, json=page_data)

    if response.status_code in [200, 201]:
        return {"status": "success", "post_id": post_id}
    else:
        return {"status": "error", "message": response.text}

def call_function(function_name, parameters):
    if function_name == "brainstorm_content":
        return brainstorm_content(**parameters)
    elif function_name == "co_write_post":
        return co_write_post(**parameters)
    elif function_name == "update_notion":
        return update_notion(**parameters)
    else:
        return {"error": "Function not found"}

def detect_intent(prompt):
    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a LinkedIn ghostwriter. Determine the user's intent based on their input. "
                    "Return 'generate' if the input is a post idea (e.g., contains 'write', 'post', 'create', or a topic). "
                    "Return 'save' if the input is 'noted' (case-insensitive). "
                    "Return 'exit' for anything else (e.g., 'stop', 'exit', or unrelated input)."
                )
            },
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

# LinkedIn content assistant with active listening
def linkedin_content_assistant():
    global latest_post
    print("Assistant: I'm here! Just say 'hello' to get started.")
    
    while True:
        user_input = input("You: ").strip().lower()
        
        print("Assistant: How can I help?")
        prompt = input("You: ").strip()
        if not prompt:
            print("How can i help you")
            continue

        intent = detect_intent(prompt)
        
        if intent == "generate":
            word_count = len(prompt.split())
            if word_count > 60:
                print(f"Assistant: Your idea is {word_count} words. Please keep it to 60 words or less for a concise post.")
                continue

            print(f"Assistant: Got your idea: '{prompt}'. Let me craft a LinkedIn post for you, just like I'd do for a client...")
            idea = prompt
            post_id = f"LI-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Brainstorm content
            questions = [
                "What key insight or lesson do you want to share?",
                "Who is your target audience for this post?",
                "What action do you want readers to take?"
            ]
            brainstorm_result = call_function("brainstorm_content", {
                "idea": idea,
                "questions": questions
            })
            answers = brainstorm_result.get("answers", [])
            if not answers:
                print("Assistant: Something went wrong while brainstorming ideas. Please try again.")
                continue

            print(f"Assistant: Here's what I came up with:\n- Insight: {answers[0]}\n- Audience: {answers[1]}\n- Action: {answers[2]}")

            # Create initial draft
            draft = f"{idea}\n\nBased on: {', '.join(answers)}"

            # Revise draft to create final post
            write_result = call_function("co_write_post", {
                "draft": draft,
                "tone": "professional, thoughtful, authentic",
                "improvements": "Keep it concise (150-280 characters), enhance clarity, add a call-to-action, include relevant hashtags"
            })
            final_post = write_result.get("revised_draft", draft)
            print(f"Assistant: Here's your polished LinkedIn post:\n{final_post}")
            print("Assistant: Want to save this to Notion? Just say 'hello' and then 'noted'. Say 'hello' again for a new post.")
            
            # Store the post in memory
            latest_post = {
                "post_id": post_id,
                "title": idea[:50] + "..." if len(idea) > 50 else idea,
                "content": final_post,
                "status": "Final"
            }

        elif intent == "save":
            if not latest_post:
                print("Assistant: No post to save yet. Say 'hello' and give me a post idea first (e.g., 'Benefits of MCP certification').")
                continue

            print("Assistant: Saving your post to Notion...")
            notion_result = call_function("update_notion", latest_post)
            if notion_result.get("status") == "success":
                print(f"Assistant: Done! Post saved to Notion with ID: {notion_result['post_id']}. Ready for posting whenever you are!")
                latest_post = None  # Clear after saving
            else:
                print(f"Assistant: Hmm, I couldn't save it to Notion: {notion_result.get('message')}. Here's the post for you to keep:\n{latest_post['content']}")
            print("Assistant: Say 'hello' to continue working together.")

        elif intent == "exit":
            print("Assistant: Alright, I'm stepping back. Say 'hello' when you need me again!")
            continue

        else:
            print("Assistant: Not sure what you meant. Try a post idea (e.g., 'Benefits of MCP certification'), 'noted' to save, or 'exit'. Say 'hello' to start again.")

# Example usage
if __name__ == "__main__":
    linkedin_content_assistant()