import os
import requests
from difflib import SequenceMatcher
from datetime import datetime, timedelta
from typing import Optional, List, Dict

COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
COINGECKO_HEADERS = {
    "accept": "application/json",
    "x-cg-pro-api-key": COINGECKO_API_KEY,
}

class CoinGeckoAPI:
    def __init__(self, coingecko_headers, coingecko_base_url):
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
        matches: List[str] = []
        highest_similarity = 0.0

        for coin in coins:
            name_similarity = self.similarity(param.lower(), coin["name"].lower())
            symbol_similarity = self.similarity(param.lower(), coin["symbol"].lower())
            id_similarity = self.similarity(param.lower(), coin["id"].lower())

            max_similarity = max(name_similarity, symbol_similarity, id_similarity)

            if max_similarity >= highest_similarity:
                highest_similarity = max_similarity
                matches.append(coin["id"])

        return matches

    def get_token_data(self, coin: str) -> Optional[List[Dict]]:
        """
        Retrieves data for a specific coin from the CoinGecko API.

        Args:
            coin (str): The coin symbol or name to search for.

        Returns:
            Optional[List[Dict]]: List of dictionaries containing coin data,
                                  or None if the coin data is not found.
        """
        try:
            formatted_coin = coin.casefold().strip()
            coins = self.get_list_of_coins()
            coins_list = self.find_best_match_ids(param=formatted_coin, coins=coins)

            if not coins_list:
                return None

            coins_data_list: List[Dict] = []
            params = {
                'vs_currency': 'usd',
                'ids': ','.join(coins_list),
                'order': 'market_cap_desc',
                'per_page': 100,
                'page': 1,
                'sparkline': 'false'
            }

            url = f"{self.coingecko_base_url}/coins/markets"
            response = requests.get(url, params=params)

            if response.status_code == 200:
                response_data = response.json()

                for coin_data in response_data:
                    if coin_data.get('market_cap'):
                        processed_coin_data = {
                            'id': coin_data.get('id'),
                            'symbol': coin_data.get('symbol'),
                            'name': coin_data.get('name'),
                            'image': coin_data.get('image'),
                            'current_price': coin_data.get('current_price'),
                            'market_cap': coin_data.get('market_cap'),
                            'market_cap_rank': coin_data.get('market_cap_rank'),
                            'fully_diluted_valuation': coin_data.get('fully_diluted_valuation'),
                            'total_volume': coin_data.get('total_volume'),
                            'high_24h': coin_data.get('high_24h'),
                            'low_24h': coin_data.get('low_24h'),
                            'price_change_24h': coin_data.get('price_change_24h'),
                            'price_change_percentage_24h': coin_data.get('price_change_percentage_24h'),
                            'market_cap_change_24h': coin_data.get('market_cap_change_24h'),
                            'market_cap_change_percentage_24h': coin_data.get('market_cap_change_percentage_24h'),
                            'circulating_supply': coin_data.get('circulating_supply'),
                            'total_supply': coin_data.get('total_supply'),
                            'max_supply': coin_data.get('max_supply'),
                            'ath': coin_data.get('ath'),
                            'ath_change_percentage': coin_data.get('ath_change_percentage'),
                            'ath_date': coin_data.get('ath_date'),
                            'atl': coin_data.get('atl'),
                            'atl_change_percentage': coin_data.get('atl_change_percentage'),
                            'atl_date': coin_data.get('atl_date'),
                            'roi': coin_data.get('roi'),
                            'last_updated': coin_data.get('last_updated'),
                            'success': True
                        }

                        if processed_coin_data['market_cap'] > 100000:
                            coins_data_list.append(processed_coin_data)

            return coins_data_list if coins_data_list else None

        except requests.RequestException as e:
            print(f"Error fetching token data: {str(e)}")
            return None
        except KeyError as e:
            print(f"Key error: {str(e)}")
            return None

    def get_coin_history(self, coin_id: str, date: Optional[str] = None) -> Optional[List[Dict]]:
        """
        Retrieves historical data for a specific coin from the CoinGecko API.

        Args:
            coin_id (str): The ID of the coin to retrieve history for.
            date (str, optional): The date for which to retrieve history (format: DD-MM-YYYY).
                                  If None, retrieves data for the past year.

        Returns:
            Optional[List[Dict]]: List of dictionaries containing historical data,
                                  or None if the data is not found or there's an error.
        """
        formatted_coin_id = coin_id.casefold().strip()
        coins_data_historical: List[Dict] = []

        if date is None:
            date = (datetime.now() - timedelta(days=365)).strftime('%d-%m-%Y')
        else:
            try:
                date = datetime.strptime(date, '%d-%m-%Y').strftime('%d-%m-%Y')
            except ValueError:
                print(f"Invalid date format. Please use DD-MM-YYYY.")
                return None

        params = {
            'date': date,
            'localization': 'false'
        }

        url = f'{self.coingecko_base_url}/coins/{formatted_coin_id}/history'

        try:
            response = requests.get(url, params=params, headers=self.coingecko_headers)
            response.raise_for_status()

            data = response.json()
            market_cap = data.get('market_data', {}).get('market_cap', {}).get('usd')

            if market_cap and market_cap > 100000:
                coin_data = {
                    'id': coin_id,
                    'date': date,
                    'price': data.get('market_data', {}).get('current_price', {}).get('usd'),
                    'market_cap': market_cap,
                    'total_volume': data.get('market_data', {}).get('total_volume', {}).get('usd')
                }
                coins_data_historical.append(coin_data)
            else:
                print(f"Market cap for {coin_id} on {date} is below threshold or not available.")

        except requests.RequestException as e:
            print(f"Request error for {coin_id}: {str(e)}")
            return None
        except KeyError as e:
            print(f"Key error for {coin_id}: {str(e)}")
            return None

        return coins_data_historical if coins_data_historical else None

# Example usage:
# cg_api = CoinGeckoAPI(COINGECKO_HEADERS, COINGECKO_BASE_URL)

# # Example of getting data for specific token
# coin = 'ripple'
# token_data = cg_api.get_token_data(coin)

# if token_data:
#     print(token_data)
# else:
#     print("Error fetching token data.")
