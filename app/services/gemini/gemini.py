import os
from typing import Dict, Generator, Optional
import google.generativeai as genai

class GeminiAPI:
    def __init__(self, verbose: bool = False):
        self.api_key: str = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in the environment variables")
        
        # Configure Gemini AI
        genai.configure(api_key=self.api_key)
        
        self.verbose = verbose
        self.model = genai.GenerativeModel('gemini-1.0-pro-latest')

    def generate_response(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None
    ) -> Generator[Dict[str, str], None, None]:
        """
        Generate a streaming response from Gemini AI.

        Args:
        user_prompt (str): The main input prompt from the user.
        system_prompt (Optional[str]): An optional system prompt to set the context.

        Yields:
        Dict[str, str]: Chunks of the response or error messages.
        """
        if self.verbose:
            print("Generating Gemini response...")

        # Combine system prompt and user prompt if both are provided
        combined_prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
        
        yield from self._stream_request(combined_prompt)

    def _stream_request(self, prompt: str) -> Generator[Dict[str, str], None, None]:
        """
        Stream the request to the Gemini API.

        Args:
        prompt (str): The combined prompt to send to the API.

        Yields:
        Dict[str, str]: Chunks of the API response.
        """
        try:
            if self.verbose:
                print("Sending request to Gemini API...")
            
            # Generate content based on the prompt
            response = self.model.generate_content(prompt, stream=True)
            
            for chunk in response:
                if chunk.parts:
                    for part in chunk.parts:
                        if hasattr(part, 'text') and part.text:
                            yield {"gemini_response": part.text}
                    
        except Exception as e:
            yield {"error": f"Error generating response: {str(e)}"}

# # Example usage
# if __name__ == "__main__":
#     try:
#         gemini = GeminiAPI(verbose=True)  # Set to False to disable debug prints
#         user_prompt = "Tell me about the importance of AI in modern technology"
#         system_prompt = "You are a knowledgeable AI expert. Provide concise and informative answers."

#         for chunk in gemini.generate_response(user_prompt, system_prompt):
#             if "content" in chunk:
#                 print(chunk["content"], end="", flush=True)
#             elif "error" in chunk:
#                 print(f"\nError: {chunk['error']}")
#         print("\nAPI request completed.")
#     except Exception as e:
#         print(f"Main execution error: {str(e)}")
