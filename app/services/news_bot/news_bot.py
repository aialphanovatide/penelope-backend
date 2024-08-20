import os
import requests
from typing import List, Dict, Optional, Set
from difflib import SequenceMatcher

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
NEWS_BOT_V2_URL = os.getenv("NEWS_BOT_V2_URL")

COINGECKO_BASE_URL = 'https://pro-api.coingecko.com/api/v3'
coingecko_headers = {
    "Content-Type": "application/json",
    "x-cg-pro-api-key": COINGECKO_API_KEY,
}

class CoinNewsFetcher:
    def __init__(self):
        self.coins = self.get_list_of_coins()
        self.all_bots = self.get_bots()

    def similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    def find_best_match_symbols(self, param: str) -> List[str]:
        """
        Finds symbols of coins that best match the given parameter using a linear search.

        Args:
            param (str): The parameter to search for.

        Returns:
            List[str]: List of symbols of coins that best match the parameter.
        """
        param_lower = param.lower()
        best_matches: Set[str] = set()
        highest_similarity = 0.0

        for coin in self.coins:
            name_similarity = self.similarity(param_lower, coin["name"].lower())
            symbol_similarity = self.similarity(param_lower, coin["symbol"].lower())
            id_similarity = self.similarity(param_lower, coin["id"].lower())

            max_similarity = max(name_similarity, symbol_similarity, id_similarity)
            
            if max_similarity > highest_similarity:
                highest_similarity = max_similarity
                best_matches = {coin["symbol"]}
            elif max_similarity == highest_similarity:
                best_matches.add(coin["symbol"])

        return list(best_matches)

    def find_ids_by_name(self, name: str) -> List[str]:
        """
        Finds IDs of bots whose names match the given name (case-insensitive).

        Args:
            name (str): The name to search for.

        Returns:
            List[str]: List of IDs matching the name, or an empty list if no matches found.
        """
        if not self.all_bots or "data" not in self.all_bots:
            raise RuntimeError("Bot data is unavailable.")

        matching_ids = [item["id"] for item in self.all_bots["data"] if item["name"].lower() == name.lower()]
        return matching_ids

    def get_list_of_coins(self) -> List[Dict]:
        """
        Fetches a list of coins from the CoinGecko API and sorts them by symbol.

        Returns:
            List[Dict]: A sorted list of coins in JSON format if successful, otherwise raises an exception.
        """
        try:
            response = requests.get(f"{COINGECKO_BASE_URL}/coins/list", headers=coingecko_headers)
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx and 5xx)
            coins_list = response.json()
            
            # Sort the list of coins by symbol
            return sorted(coins_list, key=lambda x: x['symbol'])
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error fetching list of coins: {e}")  
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {e}")

    def get_bots(self) -> Dict:
        """
        Fetches a list of bots from a specified URL.

        Returns:
            Dict: A list of bots in JSON format if successful, otherwise raises an exception.
        """
        url = f"{NEWS_BOT_V2_URL}/bots"
        headers = {"accept": "application/json"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx and 5xx)
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"An error occurred while fetching bots: {e}")

    def get_latest_news(self, coin: str, limit: int = 20) -> List[Dict]:
        """
        Retrieves the latest news articles related to the given coin symbol(s).

        Args:
            coin (str): The coin symbol to search for.
            limit (int, optional): Maximum number of news articles to retrieve per bot. Defaults to 20.

        Returns:
            List[Dict]: List of dictionaries containing 'news' and 'date' keys for each article,
                        or an empty list if no news articles are found.
        """
        symbols = self.find_best_match_symbols(coin)
        if not symbols:
            return []

        news_list: List[Dict] = []

        for symbol in symbols:
            bot_ids = self.find_ids_by_name(symbol)
            if not bot_ids:
                continue

            for bot_id in bot_ids:
                url = f"{NEWS_BOT_V2_URL}/get_articles?bot_id={bot_id}&limit={limit}"

                try:
                    response = requests.get(url)
                    response.raise_for_status()

                    data = response.json().get('data', [])
                    for article in data:
                        news_list.append({'news': article['content'], 'date': article['date']})

                except requests.exceptions.RequestException as e:
                    print(f"Error fetching articles for bot_id {bot_id}: {e}")
                    continue

        return news_list
