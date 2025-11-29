"""
Configuración de la aplicación
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Variables de configuración
PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT")
MODEL_DEPLOYMENT_NAME = os.getenv("MODEL_DEPLOYMENT_NAME")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
POLICY_AGENT_ID = os.getenv("POLICY_AGENT_ID")
KNOWLEDGE_BASE_AGENT_ID = os.getenv("KNOWLEDGE_BASE_AGENT_ID")

