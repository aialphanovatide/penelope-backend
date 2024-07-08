import os
from typing import Dict, Generator, Optional
import httpx
import json

class PerplexityAPI:
    API_URL: str = "https://api.perplexity.ai/chat/completions"

    def __init__(self, verbose: bool = False):
        self.api_key: str = os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY is not set in the environment variables")
        self.verbose = verbose

    def generate_response(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "mistral-7b-instruct",
    ) -> Generator[Dict[str, str], None, None]:
        """
        Make a streaming request to the Perplexity API.

        Args:
        model (str): The model to use for the request.
        user_prompt (str): The main content of the user's message.
        system_prompt (Optional[str]): An optional system prompt.

        Yields:
        Dict[str, str]: Chunks of the API response.
        """
        if self.verbose:
            print(f"\nGenerating Perplexity response, model: {model}")

        messages = [{"role": "user", "content": user_prompt}]
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})

        payload = {
            "model": model,
            "messages": messages,
            "stream": True
        }

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        yield from self._stream_request(payload, headers)

    def _stream_request(self, payload: Dict, headers: Dict) -> Generator[Dict[str, str], None, None]:
        """
        Stream the request to the Perplexity API.

        Args:
        payload (Dict): The request payload.
        headers (Dict): The request headers.

        Yields:
        Dict[str, str]: Chunks of the API response.
        """
        try:
            with httpx.Client(timeout=httpx.Timeout(300.0)) as client:
                if self.verbose:
                    print("Sending request to Perplexity API...")
                with client.stream("POST", self.API_URL, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    if self.verbose:
                        print(f"Response status code: {response.status_code}")
                    for line in response.iter_lines():
                        if line:
                            try:
                                json_data = json.loads(line[6:])
                                content = json_data.get('choices', [{}])[0].get('delta', {}).get('content')
                                if content:
                                    yield {"perplexity_response": content}
                            except json.JSONDecodeError:
                                yield {"error": "Failed to parse JSON response"}
        except httpx.HTTPStatusError as e:
            yield {"error": f"HTTP error occurred: {e.response.status_code} {e.response.reason_phrase}"}
        except httpx.RequestError as e:
            yield {"error": f"An error occurred while requesting {e.request.url!r}"}
        except Exception as e:
            yield {"error": f"An unexpected error occurred: {str(e)}"}


# # Example usage
# if __name__ == "__main__":
#     try:
#         perplexity = PerplexityAPI(verbose=False)  # Set to False to disable debug prints
#         model = "mistral-7b-instruct"
#         user_prompt = "Tell me about AI"
#         system_prompt = "Be concise"

#         for chunk in perplexity.generate_response(model, user_prompt, system_prompt):
#             if "content" in chunk:
#                 print(chunk["content"], end="", flush=True)
#             elif "error" in chunk:
#                 print(f"\nError: {chunk['error']}")
#         print("\nAPI request completed.")
#     except Exception as e:
#         print(f"Main execution error: {str(e)}")
