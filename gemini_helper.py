import os

import google.generativeai as genai

from database import create_database, save_response


def check_gemini_setup():
    try:
        create_database()
        genai.configure(api_key=os.environ["GOOGLE_AI_API_KEY"])
        model = genai.GenerativeModel("gemini-pro")
        chat = model.start_chat()
        user_text = "Hello, how are you?"
        response = chat.send_message(user_text)
        print("Gemini setup successful. Response received:")
        print(response.text)

        save_response(
            architecture_name="Neurosymbolic Knowledge Graph",
            provider="Gemini",
            model="gemini-pro",
            user_text=user_text,
            front_content="",
            back_content=response.text,
            system_prompt="",
        )

        return True
    except Exception as e:
        print(f"Error checking Gemini setup: {str(e)}")
        return False


if __name__ == "__main__":
    check_gemini_setup()
