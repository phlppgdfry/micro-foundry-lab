"""Lab 01: make the smallest useful call to a Microsoft Foundry model."""
import os

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()
endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
model = os.getenv("FOUNDRY_MODEL", "gpt-5-mini")

project = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
response = project.get_openai_client().responses.create(
    model=model,
    input="In one sentence, explain why evaluation matters for an AI feature.",
)
print(response.output_text)
