import os
import re
import requests
from dateutil import parser
from difflib import SequenceMatcher
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Union


COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
COINGECKO_PRO_API_URL = 'https://pro-api.coingecko.com/api/v3/coins'
COINGECKO_HEADERS = {
    "accept": "application/json",
    "x-cg-pro-api-key": COINGECKO_API_KEY,
}


class CoinGeckoAPI:
    def __init__(self, coingecko_headers: Dict[str, str], coingecko_base_url: str, verbose: bool = False):
        """
        Initialize the CoinGeckoAPI class.

        Args:
            coingecko_headers (Dict[str, str]): Headers for API requests.
            coingecko_base_url (str): Base URL for the CoinGecko API.
            verbose (bool): If True, print debug messages.
        """
        self.coingecko_headers = coingecko_headers
        self.coingecko_base_url = coingecko_base_url
        self.verbose = verbose

    def _debug_print(self, message: str):
        """Print debug messages if verbose is True."""
        if self.verbose:
            print(f"DEBUG: {message}")

    def convert_to_date(self, natural_language_date: str) -> str:
        """
        Convert a natural language date to a formatted date string.

        Args:
            natural_language_date (str): Natural language date string.

        Returns:
            str: Formatted date string (DD-MM-YYYY).
        """
        self._debug_print(f"Converting date: {natural_language_date}")
        now = datetime.now()

        # Handle specific relative dates
        if re.search(r'\blast year\b', natural_language_date, re.IGNORECASE):
            natural_language_date = natural_language_date.lower().replace("last year", str(now.year - 1))
        elif re.search(r'\btwo years ago\b', natural_language_date, re.IGNORECASE):
            natural_language_date = natural_language_date.lower().replace("two years ago", str(now.year - 2))
        elif re.search(r'\blast month\b', natural_language_date, re.IGNORECASE):
            last_month = now.replace(day=1) - timedelta(days=1)
            natural_language_date = natural_language_date.lower().replace("last month", last_month.strftime('%B'))
        elif re.search(r'\btwo months ago\b', natural_language_date, re.IGNORECASE):
            two_months_ago = now.replace(day=1) - timedelta(days=now.day + 1)
            natural_language_date = natural_language_date.lower().replace("two months ago", two_months_ago.strftime('%B'))
        elif re.search(r'\blast week\b', natural_language_date, re.IGNORECASE):
            last_week = now - timedelta(weeks=1)
            natural_language_date = natural_language_date.lower().replace("last week", last_week.strftime('%d %B %Y'))
        elif re.search(r'\btwo weeks ago\b', natural_language_date, re.IGNORECASE):
            two_weeks_ago = now - timedelta(weeks=2)
            natural_language_date = natural_language_date.lower().replace("two weeks ago", two_weeks_ago.strftime('%d %B %Y'))
        elif re.search(r'\byesterday\b', natural_language_date, re.IGNORECASE):
            yesterday = now - timedelta(days=1)
            natural_language_date = natural_language_date.lower().replace("yesterday", yesterday.strftime('%d %B %Y'))
        elif re.search(r'\btoday\b', natural_language_date, re.IGNORECASE):
            natural_language_date = natural_language_date.lower().replace("today", now.strftime('%d %B %Y'))
        elif re.search(r'\btomorrow\b', natural_language_date, re.IGNORECASE):
            tomorrow = now + timedelta(days=1)
            natural_language_date = natural_language_date.lower().replace("tomorrow", tomorrow.strftime('%d %B %Y'))
        elif re.search(r'\b(\d+) days ago\b', natural_language_date, re.IGNORECASE):
            days_ago = int(re.search(r'\b(\d+) days ago\b', natural_language_date, re.IGNORECASE).group(1))
            date_days_ago = now - timedelta(days=days_ago)
            natural_language_date = re.sub(r'\b\d+ days ago\b', date_days_ago.strftime('%d %B %Y'), natural_language_date, flags=re.IGNORECASE)
        elif re.search(r'\b(\d+) weeks ago\b', natural_language_date, re.IGNORECASE):
            weeks_ago = int(re.search(r'\b(\d+) weeks ago\b', natural_language_date, re.IGNORECASE).group(1))
            date_weeks_ago = now - timedelta(weeks=weeks_ago)
            natural_language_date = re.sub(r'\b\d+ weeks ago\b', date_weeks_ago.strftime('%d %B %Y'), natural_language_date, flags=re.IGNORECASE)
        elif re.search(r'\b(\d+) months ago\b', natural_language_date, re.IGNORECASE):
            months_ago = int(re.search(r'\b(\d+) months ago\b', natural_language_date, re.IGNORECASE).group(1))
            date_months_ago = now.replace(month=now.month - months_ago)
            natural_language_date = re.sub(r'\b\d+ months ago\b', date_months_ago.strftime('%B %Y'), natural_language_date, flags=re.IGNORECASE)
        elif re.search(r'\b(\d+) years ago\b', natural_language_date, re.IGNORECASE):
            years_ago = int(re.search(r'\b(\d+) years ago\b', natural_language_date, re.IGNORECASE).group(1))
            natural_language_date = re.sub(r'\b\d+ years ago\b', str(now.year - years_ago), natural_language_date, flags=re.IGNORECASE)

        parsed_date = parser.parse(natural_language_date)
        formatted_date = parsed_date.strftime("%d-%m-%Y")
        self._debug_print(f"Converted date: {formatted_date}")
        return formatted_date

    def get_list_of_coins(self) -> Union[List[Dict], str]:
        """
        Fetch a list of all coins from the CoinGecko API.

        Returns:
            Union[List[Dict], str]: List of dictionaries containing coin data or error message.
        """
        self._debug_print("Fetching list of coins")
        try:
            url = f"{self.coingecko_base_url}/coins/list"
            response = requests.get(url, headers=self.coingecko_headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            error_message = f"Error fetching list of coins: {str(e)}"
            self._debug_print(error_message)
            return error_message

    def get_coin_history(self, coin_id: str, date: Optional[str] = None) -> Union[List[Dict], str]:
        """
        Retrieve historical data for a specific coin.

        Args:
            coin_id (str): The ID of the coin to retrieve history for.
            date (str, optional): The date for which to retrieve history (format: DD-MM-YYYY).

        Returns:
            Union[List[Dict], str]: List of dictionaries containing historical data or error message.
        """
        self._debug_print(f"Fetching history for coin: {coin_id}, date: {date}")
        formatted_coin_id = coin_id.casefold().strip()
        list_coins_ids = self.get_list_of_coins()

        if isinstance(list_coins_ids, str):
            return list_coins_ids  # Return error message if fetching coins failed

        ids = self.find_best_match_ids(param=formatted_coin_id, coins=list_coins_ids)
        if not ids:
            return 'No matching coin IDs found.'

        coins_data_historical: List[Dict] = []

        if date is None:
            date = (datetime.now() - timedelta(days=365)).strftime('%d-%m-%Y')
        else:
            try:
                date = self.convert_to_date(date)
            except ValueError:
                return 'Invalid date format. Please use DD-MM-YYYY.'

        params = {
            'date': date,
            'localization': 'false'
        }

        self._debug_print(f"Matching IDs: {ids}")

        for id in ids:
            url = f'{COINGECKO_PRO_API_URL}/{id}/history'
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
                    self._debug_print(f'Market cap for {coin_id} on {date} is below threshold or not available.')
            except requests.RequestException as e:
                self._debug_print(f"Request error for {coin_id}: {str(e)}")
            except KeyError as e:
                self._debug_print(f"Key error for {coin_id}: {str(e)}")

        return coins_data_historical if coins_data_historical else 'Unable to get historical data'

    def similarity(self, a: str, b: str) -> float:
        """
        Compute the similarity ratio between two strings.

        Args:
            a (str): First string for comparison.
            b (str): Second string for comparison.

        Returns:
            float: Similarity ratio between 0.0 and 1.0.
        """
        return SequenceMatcher(None, a, b).ratio()

    def find_best_match_ids(self, param: str, coins: List[Dict]) -> List[str]:
        """
        Find IDs of coins that best match the given parameter.

        Args:
            param (str): The parameter to search for.
            coins (List[Dict]): List of dictionaries containing coin data.

        Returns:
            List[str]: List of IDs matching the parameter.
        """
        self._debug_print(f"Finding best matches for: {param}")
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

    def get_token_data(self, coin: str) -> Union[List[Dict], str]:
        """
        Retrieve data for a specific coin from the CoinGecko API.

        Args:
            coin (str): The coin symbol or name to search for.

        Returns:
            Union[List[Dict], str]: List of dictionaries containing coin data or error message.
        """
        self._debug_print(f"Fetching token data for: {coin}")
        try:
            formatted_coin = coin.casefold().strip()
            coins = self.get_list_of_coins()

            if isinstance(coins, str):
                return coins  # Return error message if fetching coins failed

            coins_list = self.find_best_match_ids(param=formatted_coin, coins=coins)
            if not coins_list:
                return 'No matching coins found.'

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
            response = requests.get(url, params=params, headers=self.coingecko_headers)

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

                return coins_data_list if coins_data_list else 'No token data available.'

            else:
                error_message = f"Error fetching token data: Status code {response.status_code}"
                self._debug_print(error_message)
                return error_message

        except requests.RequestException as e:
            error_message = f"Error fetching token data: {str(e)}"
            self._debug_print(error_message)
            return error_message
        except KeyError as e:
            error_message = f"Key error: {str(e)}"
            self._debug_print(error_message)
            return error_message

# # Example usage
# if __name__ == "__main__":
#     COINGECKO_HEADERS = {"Your-Headers": "Here"}
#     COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"
    
#     cg_api = CoinGeckoAPI(COINGECKO_HEADERS, COINGECKO_BASE_URL, verbose=True)
    
#     # # Example of getting data for a specific token
#     coin_name = 'xrp'
#     # token_data = cg_api.get_token_data(coin_name)
#     # print('Token data:', token_data)
    
#     # Example of getting historical data
#     historical_data = cg_api.get_coin_history(coin_name, '19-02-2023')
#     if isinstance(historical_data, list):
#         print('Historical data:', historical_data)
#     else:
#         print("Error fetching historical data:", historical_data)
