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
            RuntimeError: If the request fails or if an invalid format is specified.
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            if format == 'html':
                return response.text
            elif format == 'txt':
                soup = BeautifulSoup(response.text, 'html.parser')
                return soup.get_text().strip().replace('\n', '')
            else:
                raise ValueError("Invalid return format. Use 'html' or 'txt'.")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Request failed in scraper: {e}")
        except ValueError as e:
            raise RuntimeError(f"Value error in scrapper: {e}")



# Example usage:
# scraper = Scraper()
# url = 'https://vitalik.eth.limo/general/2024/05/31/blocksize.html'
# text_data = scraper.extract_data(url, format='txt')
# print('text_data: ', text_data)
