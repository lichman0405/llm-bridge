# app/services/model_manager.py
# The following code defines the ModelManager service, which acts as a factory and cache for LLM adapters.
# It retrieves the appropriate adapter based on the model name and manages the lifecycle of these adapters.
# Author: Shibo Li
# date: 2025-07-14
# Version 0.1.0


import yaml
import os
from pathlib import Path
from functools import lru_cache
from typing import Dict, Type, Any

from dotenv import load_dotenv

from app.adapters.base import BaseAdapter
from app.adapters.openai_compatible import OpenAICompatibleAdapter
# from app.adapters.anthropic_adapter import AnthropicAdapter

ADAPTER_CLASS_MAP = {
    "OpenAICompatibleAdapter": OpenAICompatibleAdapter,
    # "AnthropicAdapter": AnthropicAdapter,
}

def load_all_configs():
    """
    Loads all configurations from both .env and models.yml.
    """
    project_dotenv = Path(".env")
    if project_dotenv.exists():
        load_dotenv(dotenv_path=project_dotenv)
    else:
        print("Warning: .env file not found. Relying on system environment variables.")

    config_path = Path("models.yml")
    if not config_path.exists():
        raise RuntimeError("CRITICAL: Configuration file 'models.yml' not found.")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            model_configs = yaml.safe_load(f)
            if not isinstance(model_configs, dict):
                raise ValueError("models.yml should contain a dictionary of model configurations.")
            return model_configs
    except yaml.YAMLError as e:
        raise RuntimeError(f"CRITICAL: Error parsing 'models.yml': {e}")

MODEL_CONFIGS = load_all_configs()


@lru_cache(maxsize=128)
def get_adapter(model_name: str) -> BaseAdapter:
    """
    Factory for adapter instances, driven by the external models.yml configuration.
    """
    config = MODEL_CONFIGS.get(model_name)
    if not config:
        raise ValueError(f"Model '{model_name}' is not configured in models.yml.")

    adapter_name = config.get("adapter")
    if not adapter_name or adapter_name not in ADAPTER_CLASS_MAP:
        raise NotImplementedError(f"Adapter '{adapter_name}' for model '{model_name}' is not implemented.")
    adapter_class = ADAPTER_CLASS_MAP[adapter_name]

    api_key_name = config.get("api_key_name")
    base_url_name = config.get("base_url_name")

    if not api_key_name or not base_url_name:
        raise ValueError(f"Configuration for '{model_name}' in models.yml is missing 'api_key_name' or 'base_url_name'.")

    api_key = os.getenv(api_key_name)
    base_url = os.getenv(base_url_name)

    if not api_key:
        raise ValueError(f"Config Value Error: Environment variable '{api_key_name}' is not set (check your .env file).")
    if not base_url:
        raise ValueError(f"Config Value Error: Environment variable '{base_url_name}' is not set (check your .env file).")

    return adapter_class(api_key=api_key, base_url=base_url)