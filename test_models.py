
import os

API_KEY = os.getenv("API_KEY")


url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"

response = requests.get(url)

print(response.text)
