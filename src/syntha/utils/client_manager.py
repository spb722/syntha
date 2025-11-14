"""
Multi-client manager for Ollama with automatic rotation on rate limits.
"""
from pathlib import Path

import yaml
from ollama import Client


class ClientManager:
    """
    Manages multiple Ollama clients and rotates between them on rate limit errors.
    """

    def __init__(self, config_path="configs/generation_config.yaml"):
        """
        Initialize ClientManager by loading config and creating client instances.

        Args:
            config_path: Path to the generation config YAML file
        """
        self.config_path = Path(config_path)
        self.clients = []
        self.current_index = 0
        self.model = None

        self._load_config()
        self._initialize_clients()

    def _load_config(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        self.model = config['model']['name']
        self.client_configs = config['model']['clients']
        self.timeout = config['model'].get('timeout', 60)
        self.max_retries = config['model'].get('max_retries_per_client', 1)

        if not self.client_configs:
            raise ValueError("No client configurations found in config file")

    def _initialize_clients(self):
        """Create Ollama Client instances for each configuration."""
        for idx, client_config in enumerate(self.client_configs):
            host = client_config['host']
            api_key = client_config.get('api_key')

            if api_key:
                # Create client with Bearer token authentication
                client = Client(
                    host=host,
                    headers={'Authorization': f'Bearer {api_key}'}
                )
            else:
                # Create client without authentication (local instance)
                client = Client(host=host)

            self.clients.append({
                'client': client,
                'index': idx,
                'host': host,
                'has_key': bool(api_key)
            })

        print(f"✓ Initialized {len(self.clients)} Ollama client(s)")

    def chat(self, messages, options=None, format=None):
        """
        Make a chat request with automatic client rotation on rate limits.

        Args:
            messages: List of chat messages
            options: Optional dict of generation options (e.g., temperature)
            format: Optional format schema for structured output

        Returns:
            Response from successful client

        Raises:
            Exception: If all clients fail with rate limits
        """
        attempts = 0
        max_attempts = len(self.clients)
        last_error = None

        while attempts < max_attempts:
            client_info = self.clients[self.current_index]
            client = client_info['client']
            client_idx = client_info['index']

            try:
                print(f"  → Using client #{client_idx + 1} ({client_info['host']})")

                # Build chat kwargs
                chat_kwargs = {
                    'model': self.model,
                    'messages': messages,
                }
                if options:
                    chat_kwargs['options'] = options
                if format:
                    chat_kwargs['format'] = format

                response = client.chat(**chat_kwargs)

                return response

            except Exception as e:
                error_str = str(e)

                # Check if it's a rate limit error (429) or auth error (401) - both should rotate
                is_rate_limit = "429" in error_str or "rate limit" in error_str.lower()
                is_auth_error = "401" in error_str or "unauthorized" in error_str.lower()

                if is_rate_limit or is_auth_error:
                    if is_rate_limit:
                        print(f"  ✗ Client #{client_idx + 1} hit rate limit")
                    elif is_auth_error:
                        print(f"  ✗ Client #{client_idx + 1} unauthorized (invalid/expired API key)")

                    last_error = e

                    # Rotate to next client
                    self.current_index = (self.current_index + 1) % len(self.clients)
                    attempts += 1

                    if attempts < max_attempts:
                        print(f"  ↻ Rotating to next client...")
                else:
                    # Other errors (network, model not found, etc.) - re-raise immediately
                    raise

        # All clients exhausted
        raise Exception(
            f"All {len(self.clients)} clients failed (rate limits or auth errors). "
            f"Last error: {last_error}"
        )

    def get_current_client_info(self):
        """Get information about the currently active client."""
        client_info = self.clients[self.current_index]
        return f"Client #{client_info['index'] + 1} ({client_info['host']})"
