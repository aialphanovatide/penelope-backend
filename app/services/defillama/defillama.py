import os
import requests
from difflib import SequenceMatcher
from typing import Optional, List, Dict

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
COINGECKO_HEADERS = {
    "accept": "application/json",
    "x-cg-pro-api-key": COINGECKO_API_KEY,
}

class LlamaChainFetcher:
    def __init__(self, coingecko_headers, coingecko_base_url):
        self.url = "https://api.llama.fi/v2/chains"
        self.coingecko_headers = coingecko_headers
        self.coingecko_base_url = coingecko_base_url

    def get_list_of_coins(self) -> Optional[List[Dict]]:
        """
        Fetches a list of all coins from the CoinGecko API.

        Returns:
            Optional[List[Dict]]: List of dictionaries containing coin data,
                                  or None if the request fails.
        """
        try:
            url = f"{self.coingecko_base_url}/coins/list"
            response = requests.get(url, headers=self.coingecko_headers)
            response.raise_for_status()  # Raise an error for bad responses

            if response.status_code == 200:
                return response.json()
            return None

        except requests.RequestException as e:
            print(f"Error fetching list of coins: {str(e)}")
            return None

    def similarity(self, a: str, b: str) -> float:
        """
        Computes the similarity ratio between two strings.

        Args:
            a (str): First string for comparison.
            b (str): Second string for comparison.

        Returns:
            float: Similarity ratio between 0.0 and 1.0.
        """
        return SequenceMatcher(None, a, b).ratio()

    def find_best_match_ids(self, param: str, coins: List[Dict]) -> List[str]:
        """
        Finds IDs of coins that best match the given parameter.

        Args:
            param (str): The parameter to search for.
            coins (List[Dict]): List of dictionaries containing coin data.

        Returns:
            List[str]: List of IDs matching the parameter.
        """
        matches = set()
        highest_similarity = 0.0

        for coin in coins:
            name_similarity = self.similarity(param.lower(), coin["name"].lower())
            symbol_similarity = self.similarity(param.lower(), coin["symbol"].lower())
            id_similarity = self.similarity(param.lower(), coin["id"].lower())

            max_similarity = max(name_similarity, symbol_similarity, id_similarity)

            if max_similarity >= highest_similarity:
                highest_similarity = max_similarity
                matches.add(coin["symbol"])

        return list(matches)

    def get_llama_chains(self, token_id):
        try:
            formatted_token_id = str(token_id).casefold()

            coins = self.get_list_of_coins()
            if coins is None:
                print("Failed to fetch coins list")
                return None
            
            coins_list = self.find_best_match_ids(param=formatted_token_id, coins=coins)
            coins_tvl = []
        
            response = requests.get(self.url)

            if response.status_code == 200:
                chains = response.json()
                sorted_data = sorted(chains, key=lambda item: (item.get('tokenSymbol') is None, item.get('tokenSymbol', '')))

                for chain in sorted_data:
                    if chain:
                        chain_symbol = chain.get('tokenSymbol', '')
                        if chain_symbol and any(coin.lower() == chain_symbol.lower() for coin in coins_list):
                            coins_tvl.append({
                                'id': chain.get('gecko_id'),
                                'name': chain.get('name'),
                                'tvl': chain.get('tvl')
                            })
            
            return coins_tvl
        
        except requests.RequestException as e:
            print(f"Request error: {str(e)}")
            return None
        
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            return None

    @staticmethod
    def get_token_symbol(item):
        token_symbol = item.get('tokenSymbol')
        return token_symbol.lower() if token_symbol is not None else ''
    


# fetcher = LlamaChainFetcher(coingecko_base_url=COINGECKO_BASE_URL,
#                             coingecko_headers=COINGECKO_HEADERS
#                             )
# result = fetcher.get_llama_chains("solana")

# if result is not None:
#     print(result)
# else:
#     print("No valid result returned", result)

