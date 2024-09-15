import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

def search_walmart(keyword):
    url = f"https://www.walmart.com/search?q={keyword}&sort=best_seller"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    results = []
    items = soup.find_all('div', {'data-item-id': True})
    
    for item in items[:5]:  # Limit to first 5 results for demonstration
        item_id = item.get('data-item-id')
        title = item.find('span', class_='w_DJ')
        price = item.find('div', class_='b black f5 mr1 mr2-xl lh-copy f4-l')
        
        if title and price:
            results.append({
                'Item': title.text.strip(),
                'Online Price': price.text.strip(),
                'Item ID': item_id
            })
    
    return results

def check_local_availability(item_id, zip_code):
    url = f"https://www.walmart.com/terra-firma/item/{item_id}/location/{zip_code}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    data = json.loads(response.text)
    
    if 'data' in data and 'inStore' in data['data']:
        in_store = data['data']['inStore']
        if in_store and 'price' in in_store:
            return in_store['price']
    return "Not available"

st.title("Walmart Bestsellers Near 48864")

keyword = st.sidebar.text_input("Enter keyword for bestsellers:")

if keyword:
    st.write(f"Searching for '{keyword}' bestsellers...")
    results = search_walmart(keyword)
    
    if results:
        for item in results:
            local_price = check_local_availability(item['Item ID'], '48864')
            item['Local Price'] = f"${local_price}" if isinstance(local_price, (int, float)) else local_price
        
        df = pd.DataFrame(results)
        df = df.drop(columns=['Item ID'])  # Remove Item ID from display
        st.table(df)
    else:
        st.write("No results found. Try a different keyword.")
else:
    st.write("Enter a keyword in the sidebar to search for bestsellers.")
    
