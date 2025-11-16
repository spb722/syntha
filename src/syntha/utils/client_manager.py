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
                # Create client with Bearer token authentication and timeout
                client = Client(
                    host=host,
                    headers={'Authorization': f'Bearer {api_key}'},
                    timeout=self.timeout
                )
            else:
                # Create client without authentication (local instance) with timeout
                client = Client(
                    host=host,
                    timeout=self.timeout
                )

            self.clients.append({
                'client': client,
                'index': idx,
                'host': host,
                'has_key': bool(api_key)
            })

        print(f"✓ Initialized {len(self.clients)} Ollama client(s) with {self.timeout}s timeout")

    def chat(self, messages, options=None, format=None):
        """
        Make a chat request with automatic retry and client rotation.

        Retry strategy:
        - Timeout errors: Retry 5 times on the same client, then rotate to next
        - Auth errors (401): Rotate immediately to next client
        - Rate limit (429): Rotate immediately to next client
        - Other errors: Raise immediately

        Args:
            messages: List of chat messages
            options: Optional dict of generation options (e.g., temperature)
            format: Optional format schema for structured output

        Returns:
            Response from successful client

        Raises:
            Exception: If all clients fail after retries
        """
        client_attempts = 0
        max_client_attempts = len(self.clients)
        last_error = None
        timeout_retries_per_client = 5  # Retry 5 times for timeout errors

        while client_attempts < max_client_attempts:
            client_info = self.clients[self.current_index]
            client = client_info['client']
            client_idx = client_info['index']

            # Try current client with retries for timeout errors
            for retry in range(timeout_retries_per_client):
                try:
                    if retry == 0:
                        print(f"  → Using client #{client_idx + 1} ({client_info['host']})")
                    else:
                        print(f"  ⟳ Retry {retry}/{timeout_retries_per_client - 1} on client #{client_idx + 1}")

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

                    # Success! Return response
                    return response

                except Exception as e:
                    error_str = str(e)
                    last_error = e

                    # Check error type
                    is_timeout = (
                        "timeout" in error_str.lower() or
                        "timed out" in error_str.lower() or
                        "TimeoutError" in str(type(e)) or
                        "ReadTimeout" in str(type(e))
                    )
                    is_rate_limit = "429" in error_str or "rate limit" in error_str.lower()
                    is_auth_error = "401" in error_str or "unauthorized" in error_str.lower()

                    if is_timeout:
                        # Timeout error - retry on same client
                        if retry < timeout_retries_per_client - 1:
                            print(f"  ⚠ Client #{client_idx + 1} timeout, retrying...")
                            continue  # Retry on same client
                        else:
                            # Max retries reached for this client
                            print(f"  ✗ Client #{client_idx + 1} failed after {timeout_retries_per_client} timeout retries")
                            break  # Move to next client

                    elif is_auth_error:
                        # Auth error - rotate immediately (no retry)
                        print(f"  ✗ Client #{client_idx + 1} unauthorized (invalid/expired API key)")
                        break  # Move to next client

                    elif is_rate_limit:
                        # Rate limit - rotate immediately (no retry)
                        print(f"  ✗ Client #{client_idx + 1} hit rate limit")
                        break  # Move to next client

                    else:
                        # Other errors (network, model not found, etc.) - re-raise immediately
                        raise

            # Rotate to next client
            self.current_index = (self.current_index + 1) % len(self.clients)
            client_attempts += 1

            if client_attempts < max_client_attempts:
                print(f"  ↻ Rotating to next client...")

        # All clients exhausted
        raise Exception(
            f"All {len(self.clients)} clients failed after retries. "
            f"Last error: {last_error}"
        )

    def get_current_client_info(self):
        """Get information about the currently active client."""
        client_info = self.clients[self.current_index]
        return f"Client #{client_info['index'] + 1} ({client_info['host']})"
