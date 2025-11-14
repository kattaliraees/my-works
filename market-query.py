import requests
from datetime import datetime, timedelta
import json

class CryptoDataFetcher:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': api_key,
        }
    
    def get_crypto_data(self, symbols, min_market_cap=None):
        """
        Get current price and 24h data for given crypto symbols
        
        Args:
            symbols: List of crypto symbols (e.g., ['BTC', 'ETH', 'SOL'])
            min_market_cap: Minimum market cap filter in USD (e.g., 5000000000 for 5B)
        """
        url = f"{self.base_url}/cryptocurrency/quotes/latest"
        
        params = {
            'symbol': ','.join(symbols),
            'convert': 'USD'
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = {}
            filtered_count = 0
            
            for symbol in symbols:
                if symbol in data['data']:
                    crypto = data['data'][symbol]
                    quote = crypto['quote']['USD']
                    market_cap = quote['market_cap']
                    
                    # Apply market cap filter
                    if min_market_cap is not None and market_cap is not None and market_cap < min_market_cap:
                        filtered_count += 1
                        print(f"  Filtered out {crypto['name']} ({symbol}): Market cap ${market_cap:,.0f} < ${min_market_cap:,.0f}")
                        continue
                    
                    results[symbol] = {
                        'name': crypto['name'],
                        'symbol': crypto['symbol'],
                        'current_price': quote['price'],
                        'volume_24h': quote['volume_24h'],
                        'percent_change_24h': quote['percent_change_24h'],
                        'percent_change_7d': quote['percent_change_7d'],
                        'percent_change_30d': quote['percent_change_30d'],
                        'market_cap': market_cap,
                        'last_updated': quote['last_updated']
                    }
            
            if filtered_count > 0:
                print(f"\nFiltered out {filtered_count} coin(s) due to market cap threshold")
            
            return results
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data: {e}")
            return None
    
    def get_historical_price(self, symbol, days_ago):
        """
        Get historical price for a specific date
        Note: Historical data requires a paid CoinMarketCap plan
        
        Args:
            symbol: Crypto symbol (e.g., 'BTC')
            days_ago: Number of days ago
        """
        url = f"{self.base_url}/cryptocurrency/quotes/historical"
        
        target_date = datetime.now() - timedelta(days=days_ago)
        
        params = {
            'symbol': symbol,
            'time_start': target_date.strftime('%Y-%m-%d'),
            'time_end': target_date.strftime('%Y-%m-%d'),
            'convert': 'USD'
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data and 'quotes' in data['data'] and len(data['data']['quotes']) > 0:
                quote = data['data']['quotes'][0]['quote']['USD']
                return quote['price']
            return None
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching historical data: {e}")
            return None
    
    def get_complete_data(self, symbols, min_market_cap=None):
        """
        Get complete data including current and historical prices
        
        Args:
            symbols: List of crypto symbols
            min_market_cap: Minimum market cap filter in USD (e.g., 5000000000 for 5B)
        """
        current_data = self.get_crypto_data(symbols, min_market_cap)
        
        if not current_data:
            return None
        
        # Add historical data
        for symbol in symbols:
            if symbol in current_data:
                print(f"Fetching historical data for {symbol}...")
                
                # Get historical prices (1 month, 3 months, 6 months ago)
                price_1m = self.get_historical_price(symbol, 30)
                price_3m = self.get_historical_price(symbol, 90)
                price_6m = self.get_historical_price(symbol, 180)
                
                current_data[symbol]['price_1_month_ago'] = price_1m
                current_data[symbol]['price_3_months_ago'] = price_3m
                current_data[symbol]['price_6_months_ago'] = price_6m
                
                # Calculate percentage changes if historical data available
                current_price = current_data[symbol]['current_price']
                
                if price_1m:
                    current_data[symbol]['change_1m_percent'] = ((current_price - price_1m) / price_1m) * 100
                if price_3m:
                    current_data[symbol]['change_3m_percent'] = ((current_price - price_3m) / price_3m) * 100
                if price_6m:
                    current_data[symbol]['change_6m_percent'] = ((current_price - price_6m) / price_6m) * 100
        
        return current_data
    
    def display_data(self, data):
        """Display the crypto data in a readable format"""
        for symbol, info in data.items():
            print(f"\n{'='*60}")
            print(f"{info['name']} ({symbol})")
            print(f"{'='*60}")
            if info['current_price'] is not None:
                print(f"Current Price: ${info['current_price']:,.2f}")
            if info['market_cap'] is not None:
                print(f"Market Cap: ${info['market_cap']:,.0f}")
            print(f"24h Volume: ${info['volume_24h']:,.0f}")
            print(f"\n24h Change: {info['percent_change_24h']:.2f}%")
            print(f"7d Change: {info['percent_change_7d']:.2f}%")
            print(f"30d Change: {info['percent_change_30d']:.2f}%")
            
            if 'price_1_month_ago' in info and info['price_1_month_ago']:
                print(f"\n1 Month Ago: ${info['price_1_month_ago']:,.2f} ({info.get('change_1m_percent', 0):.2f}%)")
            if 'price_3_months_ago' in info and info['price_3_months_ago']:
                print(f"3 Months Ago: ${info['price_3_months_ago']:,.2f} ({info.get('change_3m_percent', 0):.2f}%)")
            if 'price_6_months_ago' in info and info['price_6_months_ago']:
                print(f"6 Months Ago: ${info['price_6_months_ago']:,.2f} ({info.get('change_6m_percent', 0):.2f}%)")
            
            print(f"\nLast Updated: {info['last_updated']}")


def load_crypto_data(filename='crypto_data.json'):
    """Load crypto data from JSON file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {filename} not found")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {filename}")
        return None


def change_percent_filter(period, threshold_str, filename='crypto_data.json'):
    """
    Filter and print coins based on percentage change threshold
    
    Args:
        period: Time period ('24h', '7d', '30d', '1m', '3m', '6m')
        threshold_str: Threshold as string (e.g., '-10%', '10%')
        filename: JSON file to read from
    
    Returns:
        List of filtered coins
    """
    # Load data from JSON
    data = load_crypto_data(filename)
    if not data:
        return []
    
    # Parse threshold
    threshold = float(threshold_str.strip('%'))
    
    # Map period to data field
    period_map = {
        '24h': 'percent_change_24h',
        '7d': 'percent_change_7d',
        '30d': 'percent_change_30d',
        '1m': 'change_1m_percent',
        '3m': 'change_3m_percent',
        '6m': 'change_6m_percent'
    }
    
    if period not in period_map:
        print(f"Error: Invalid period '{period}'. Use: 24h, 7d, 30d, 1m, 3m, or 6m")
        return []
    
    field = period_map[period]
    filtered_coins = []
    
    # Filter coins based on threshold
    for symbol, info in data.items():
        if field not in info or info[field] is None:
            continue
        
        change_percent = info[field]
        
        # If threshold is negative, filter for values <= threshold
        # If threshold is positive, filter for values >= threshold
        if threshold < 0:
            if change_percent <= threshold:
                filtered_coins.append((symbol, info, change_percent))
        else:
            if change_percent >= threshold:
                filtered_coins.append((symbol, info, change_percent))
    
    # Sort by change percent
    filtered_coins.sort(key=lambda x: x[2])
    
    # Print results
    if filtered_coins:
        print(f"\n{'='*70}")
        if threshold < 0:
            print(f"Coins with {period} change <= {threshold}%")
        else:
            print(f"Coins with {period} change >= {threshold}%")
        print(f"{'='*70}")
        
        for symbol, info, change in filtered_coins:
            print(f"\n{info['name']} ({symbol})")
            if info['current_price'] is not None:
                print(f"  Current Price: ${info['current_price']:,.2f}")
            print(f"  {period.upper()} Change: {change:.2f}%")
            
            # Show additional context
            if '24h' in period or '7d' in period or '30d' in period:
                print(f"  24h: {info.get('percent_change_24h', 0):.2f}% | "
                      f"7d: {info.get('percent_change_7d', 0):.2f}% | "
                      f"30d: {info.get('percent_change_30d', 0):.2f}%")
        
        print(f"\n{'='*70}")
        print(f"Total coins found: {len(filtered_coins)}")
    else:
        print(f"\nNo coins found with {period} change {'<=' if threshold < 0 else '>='} {threshold}%")
    
    return filtered_coins


# Example usage
if __name__ == "__main__":
    # Replace with your CoinMarketCap API key
    API_KEY = "aefa5d3427b441be8adc5c0478508637"
    
    # Array of crypto symbols to fetch
    crypto_symbols = ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'ADA', 'DOGE', 'DOT', 'MATIC', 'LTC', 'AVAX', 'SHIB', 'TRX', 'UNI', 'LINK', 'XLM', 'ATOM', 'VET', 'ICP', 'FIL', 'ALGO', 'XTZ', 'EGLD', 'AAVE', 'MKR']
    
    # Set minimum market cap filter (5 billion USD)
    MIN_MARKET_CAP = 5_000_000_000  # 5B
    # Or use: MIN_MARKET_CAP = 1_000_000_000  # 1B
    # Or use: MIN_MARKET_CAP = 10_000_000_000  # 10B
    # Or use: MIN_MARKET_CAP = None  # No filter
    
    # Initialize fetcher
    fetcher = CryptoDataFetcher(API_KEY)
    
    # Get complete data (current + historical) with market cap filter
    print("Fetching cryptocurrency data...")
    print(f"Market cap filter: ${MIN_MARKET_CAP:,.0f} or above\n" if MIN_MARKET_CAP else "No market cap filter\n")
    
    data = fetcher.get_complete_data(crypto_symbols, min_market_cap=MIN_MARKET_CAP)
    
    if data:
        # Display the data
        fetcher.display_data(data)
        
        # Save to JSON file
        with open('crypto_data.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n\nData saved to crypto_data.json ({len(data)} coins)")
    else:
        print("Failed to fetch data")
    
    print("\n" + "="*70)
    print("FILTERING EXAMPLES")
    print("="*70)
    
    # Example filter usage
    # Find coins with 7d change <= -10%
    print("\n\n1. Finding coins with 7d drop of 10% or more:")
    change_percent_filter('7d', '-10%')
    
    # Find coins with 24h change >= 10%
    print("\n\n2. Finding coins with 24h gain of 10% or more:")
    change_percent_filter('24h', '10%')
    
    # Find coins with 30d change <= -5%
    print("\n\n3. Finding coins with 30d drop of 5% or more:")
    change_percent_filter('30d', '-5%')
    
    # Find coins with 1m change >= 20%
    print("\n\n4. Finding coins with 1 month gain of 20% or more:")
    change_percent_filter('1m', '20%')