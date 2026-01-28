import streamlit as st
import requests
import io
import base64
from dotenv import load_dotenv
import google.generativeai as genai
# Load environment variables from .env file
LLM="gemini-pro"
# Get the API key from environment variables
subscription_key = "731bcfac-aef2-4541-88ee-1dc114b017a4"
xai_api_key = "AIzaSyCF9rosV79abKK62T49SaUsLdD2iapUA4s" #gemini
sarvamurl = "https://api.sarvam.ai/text-to-speech"
sarvamheaders = {
    "accept": "application/json",
    "content-type": "application/json",
    "api-subscription-key": subscription_key
}
# Initialize Gemini client
# Configure Gemini API key

genai.configure(api_key=xai_api_key)
LLMclient = genai.GenerativeModel(LLM)
# Function to send audio to Sarvam API for speech recognition
def process_with_llm(text):
    try:
        response = LLMclient.generate_content(text)
        return response.text
    except Exception as e:
        return f"An error occurred: {str(e)}" 