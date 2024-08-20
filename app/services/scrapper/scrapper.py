import requests
from bs4 import BeautifulSoup
from typing import Optional

class Scraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

    def extract_data(self, url: str, format: Optional[str] = 'html') -> str:
        """
        Extracts data from a given URL.

        Args:
            url (str): The URL to scrape.
            format (str, optional): The format of the returned data. Defaults to 'html'.
                                    Can be 'html' for raw HTML or 'txt' for text extracted from HTML.

        Returns:
            str: Extracted data from the URL.

        Raises:
            ValueError: If an invalid format is specified.
            RuntimeError: If the request fails or if the URL returns an unexpected status.
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx and 5xx)

            if format == 'html':
                return response.text
            elif format == 'txt':
                soup = BeautifulSoup(response.text, 'html.parser')
                return soup.get_text().strip().replace('\n', '')
            else:
                raise ValueError("Invalid format specified. Use 'html' or 'txt'.")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Request failed: {e}")
        except ValueError as e:
            raise ValueError(f"Value error: {e}")

# Example usage:
# if __name__ == "__main__":
#     scraper = Scraper()
#     url = 'https://vitalik.eth.limo/general/2024/05/31/blocksize.html'
#     try:
#         text_data = scraper.extract_data(url, format='txt')
#         print('Extracted text data:', text_data)
#     except (RuntimeError, ValueError) as e:
#         print(f"Error occurred: {e}")
