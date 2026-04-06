import json
import os
import ast
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory for database files
DATABASE_DIR = 'database'

def load_data(filename):
    """Load data from a JSON file in the database directory."""
    filepath = os.path.join(DATABASE_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Database file {filename} not found.")
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

# Fashion Store Tools
def check_out_of_stock(item_name):
    """
    Check if an item is out of stock in the fashion store.
    Reads from fashion.json and returns True if the item is not in stock.
    """
    try:
        data = load_data('fashion.json')
        for item in data:
            if item['name'].lower() == item_name.lower():
                return not item.get('in_stock', True)
        return None  # Item not found
    except Exception as e:
        return f"Error: {str(e)}"

def discount(item_name):
    """
    Get the discount percentage for an item in the fashion store.
    Reads from fashion.json and returns the discount value.
    """
    try:
        data = load_data('fashion.json')
        for item in data:
            if item['name'].lower() == item_name.lower():
                return item.get('discount', 0.0)
        return None
    except Exception as e:
        return f"Error: {str(e)}"

def price(item_name):
    """
    Get the price of an item in the fashion store.
    Reads from fashion.json and returns a dict with name, price, discount if found.
    """
    try:
        data = load_data('fashion.json')
        for item in data:
            if item['name'].lower() == item_name.lower():
                return {"name": item['name'], "price": item['price'], "discount": item.get('discount', 0.0)}
        return None
    except Exception as e:
        return f"Error: {str(e)}"

def search_fashion(criteria):
    """
    Search fashion items based on criteria, e.g., price < 70.
    Criteria is a string like "price < 70".
    Returns list of matching items with name, price, discount.
    """
    try:
        data = load_data('fashion.json')
        results = []
        criteria = criteria.replace(" ", "")  # Remove spaces
        if "<" in criteria:
            key, value = criteria.split("<", 1)
            if key == "price":
                threshold = float(value)
                for item in data:
                    if item['price'] < threshold:
                        results.append({"name": item['name'], "price": item['price'], "discount": item.get('discount', 0.0)})
        elif ">" in criteria:
            key, value = criteria.split(">", 1)
            if key == "price":
                threshold = float(value)
                for item in data:
                    if item['price'] > threshold:
                        results.append({"name": item['name'], "price": item['price'], "discount": item.get('discount', 0.0)})
        return results[:5]  # Limit to 5 results
    except Exception as e:
        return f"Error: {str(e)}"

# Course Registration Tools
def prerequisite_check(course_name):
    """
    Check prerequisites for a course.
    Reads from course.json and returns the list of prerequisites.
    """
    try:
        data = load_data('course.json')
        for course in data:
            if course['name'].lower() == course_name.lower():
                return course.get('prerequisites', [])
        return None
    except Exception as e:
        return f"Error: {str(e)}"

def elective_check(course_name):
    """
    Check if a course is elective.
    Reads from course.json and returns True if it's elective.
    """
    try:
        data = load_data('course.json')
        for course in data:
            if course['name'].lower() == course_name.lower():
                return course.get('type') == 'elective'
        return None
    except Exception as e:
        return f"Error: {str(e)}"

def course_price(course_name):
    """
    Get the price of a course.
    Reads from course.json and returns the price.
    """
    try:
        data = load_data('course.json')
        for course in data:
            if course['name'].lower() == course_name.lower():
                return {"name": course['name'], "price": course['price'], "credits": course.get('credits', 0)}
        return None
    except Exception as e:
        return f"Error: {str(e)}"

def credit_count(course_name):
    """
    Get the credit count of a course.
    Reads from course.json and returns the credits.
    """
    try:
        data = load_data('course.json')
        for course in data:
            if course['name'].lower() == course_name.lower():
                return course.get('credits', 0)
        return None
    except Exception as e:
        return f"Error: {str(e)}"

def optimize_plan(courses):
    """
    Optimize a course plan by calculating total credits and cost.
    Takes a list of course names, reads from course.json, and returns total credits and cost.
    """
    try:
        data = load_data('course.json')
        total_credits = 0
        total_cost = 0.0
        for course_name in courses:
            for course in data:
                if course['name'].lower() == course_name.lower():
                    total_credits += course.get('credits', 0)
                    total_cost += course.get('price', 0.0)
                    break
        return {"total_credits": total_credits, "total_cost": total_cost}
    except Exception as e:
        return f"Error: {str(e)}"

# Restaurant Search Tools
def is_open(restaurant_name):
    """
    Check if a restaurant is open (simplified: always assume open for demo).
    Reads from restaurant.json and returns open hours.
    """
    try:
        data = load_data('restaurant.json')
        for restaurant in data:
            if restaurant['name'].lower() == restaurant_name.lower():
                return restaurant.get('open_hours', 'Unknown')
        return None
    except Exception as e:
        return f"Error: {str(e)}"

def average_price(restaurant_name):
    """
    Get the average price of a restaurant.
    Reads from restaurant.json and returns the average price.
    """
    try:
        data = load_data('restaurant.json')
        for restaurant in data:
            if restaurant['name'].lower() == restaurant_name.lower():
                return restaurant.get('average_price', 0.0)
        return None
    except Exception as e:
        return f"Error: {str(e)}"

def location_search(location):
    """
    Search restaurants by location.
    Reads from restaurant.json and returns list of restaurants matching the location.
    """
    try:
        data = load_data('restaurant.json')
        results = [r['name'] for r in data if location.lower() in r.get('address', '').lower()]
        return results[:5]  # Limit to 5
    except Exception as e:
        return f"Error: {str(e)}"

# Travel Booking Tools
def flight_price(destination):
    """
    Get flight price to a destination.
    Reads from travel.json and returns the price for flights.
    """
    try:
        data = load_data('travel.json')
        for item in data:
            if item.get('type') == 'flight' and destination.lower() in item.get('name', '').lower():
                return item.get('price', 0.0)
        return None
    except Exception as e:
        return f"Error: {str(e)}"

def hotel_availability(destination):
    """
    Check hotel availability in a destination.
    Reads from travel.json and returns availability for hotels.
    """
    try:
        data = load_data('travel.json')
        for item in data:
            if item.get('type') == 'hotel' and destination.lower() in item.get('name', '').lower():
                return item.get('available', False)
        return None
    except Exception as e:
        return f"Error: {str(e)}"

def discount_package(destination):
    """
    Get discount for travel packages to a destination.
    Reads from travel.json and returns the discount.
    """
    try:
        data = load_data('travel.json')
        for item in data:
            if destination.lower() in item.get('name', '').lower():
                return item.get('discount', 0.0)
        return None
    except Exception as e:
        return f"Error: {str(e)}"

# Banking Services Tools
def check_balance(account_id):
    """
    Check balance of an account.
    Reads from banking.json and returns the balance.
    """
    try:
        data = load_data('banking.json')
        for account in data:
            if account['account_id'] == account_id:
                return account.get('balance', 0.0)
        return None
    except Exception as e:
        return f"Error: {str(e)}"

def loan_interest(account_id):
    """
    Get loan interest rate for an account.
    Reads from banking.json and returns the interest rate.
    """
    try:
        data = load_data('banking.json')
        for account in data:
            if account['account_id'] == account_id:
                return account.get('loan_interest', 0.0)
        return None
    except Exception as e:
        return f"Error: {str(e)}"

def currency_exchange(account_id):
    """
    Get currency exchange rate for an account.
    Reads from banking.json and returns the exchange rate.
    """
    try:
        data = load_data('banking.json')
        for account in data:
            if account['account_id'] == account_id:
                return account.get('currency_exchange_rate', 1.0)
        return None
    except Exception as e:
        return f"Error: {str(e)}"

# GitHub API Tools
def get_github_token():
    """Get GitHub token from environment variables."""
    return os.getenv('GITHUB_TOKEN')

def create_github_issue(repo_owner, repo_name, title, body):
    """
    Create a new issue on a GitHub repository.
    Args: repo_owner (str), repo_name (str), title (str), body (str)
    Returns: dict with issue details or error message
    """
    token = get_github_token()
    if not token:
        return "Error: GitHub token not found in environment variables."
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "title": title,
        "body": body
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            return response.json()
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

def get_github_repo_info(repo_owner, repo_name):
    """
    Get information about a GitHub repository.
    Args: repo_owner (str), repo_name (str)
    Returns: dict with repo details or error message
    """
    token = get_github_token()
    if not token:
        return "Error: GitHub token not found in environment variables."
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

def list_github_issues(repo_owner, repo_name, state='open'):
    """
    List issues in a GitHub repository.
    Args: repo_owner (str), repo_name (str), state (str) - 'open', 'closed', 'all'
    Returns: list of issues or error message
    """
    token = get_github_token()
    if not token:
        return "Error: GitHub token not found in environment variables."
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    params = {"state": state}
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"