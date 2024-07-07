import os
from typing import Dict, Generator, Optional
from openai import APIError, RateLimitError, APIConnectionError, OpenAI

class ChatGPTAPI:
    def __init__(self, verbose: bool = False):
        self.api_key: str = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is not set in the environment variables")
        self.client = OpenAI(api_key=self.api_key)
        self.verbose = verbose

    def generate_response(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        model: str = "gpt-4o",
        temperature: float = 0.6,
        max_tokens: int = 1024
    ) -> Generator[Dict[str, str], None, None]:
        """
        Send prompts to ChatGPT and get a streaming response.

        Args:
        user_prompt (str): The main input prompt from the user.
        system_prompt (Optional[str]): An optional system prompt to set the context.
        model (str): The model to use (default: "gpt-4").
        temperature (float): Controls randomness (0.0 to 1.0, default: 0.6).
        max_tokens (int): Maximum number of tokens in the response (default: 1024).

        Yields:
        Dict[str, str]: Chunks of the response or error messages.
        """
        if self.verbose:
            print(f"Generating ChatGPT response, model: {model}")

        messages = [{"role": "user", "content": user_prompt}]
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})

        yield from self._stream_request(messages, model, temperature, max_tokens)

    def _stream_request(
        self, 
        messages: list, 
        model: str, 
        temperature: float, 
        max_tokens: int
    ) -> Generator[Dict[str, str], None, None]:
        """
        Stream the request to the OpenAI API.

        Args:
        messages (list): The messages to send to the API.
        model (str): The model to use.
        temperature (float): Controls randomness.
        max_tokens (int): Maximum number of tokens in the response.

        Yields:
        Dict[str, str]: Chunks of the API response.
        """
        try:
            if self.verbose:
                print("Sending request to OpenAI API...")
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )

            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    yield {"openai_response": chunk.choices[0].delta.content}

        except (APIConnectionError, RateLimitError, APIError) as e:
            yield {"error": f"OpenAI API error: {str(e)}"}
        except Exception as e:
            yield {"error": f"Unexpected error: {str(e)}"}

# # Example usage
# if __name__ == "__main__":
#     try:
#         chatgpt = ChatGPTAPI(verbose=True)  # Set to False to disable debug prints
#         user_prompt = "Tell me about the importance of AI in modern technology"
#         system_prompt = "You are a knowledgeable AI expert. Provide concise and informative answers."

#         for chunk in chatgpt.generate_response(user_prompt, system_prompt):
#             if "content" in chunk:
#                 print(chunk["content"], end="", flush=True)
#             elif "error" in chunk:
#                 print(f"\nError: {chunk['error']}")
#         print("\nAPI request completed.")
#     except Exception as e:
#         print(f"Main execution error: {str(e)}")
