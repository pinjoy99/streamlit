import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

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
        title = item.find('span', class_='w_DJ')
        price = item.find('div', class_='b black f5 mr1 mr2-xl lh-copy f4-l')
        
        if title and price:
            results.append({
                'Item': title.text.strip(),
                'Online Price': price.text.strip(),
            })
    
    return results

def check_local_availability(item_name, zip_code):
    # This is a mock function. In a real scenario, you'd need to interact with Walmart's API
    # or scrape their website to get actual local availability and pricing.
    return "Not available" if len(item_name) % 2 == 0 else f"${float(len(item_name)) + 0.99:.2f}"

st.title("Walmart Bestsellers Near 48864")

keyword = st.sidebar.text_input("Enter keyword for bestsellers:")

if keyword:
    st.write(f"Searching for '{keyword}' bestsellers...")
    results = search_walmart(keyword)
    
    if results:
        for item in results:
            local_price = check_local_availability(item['Item'], '48864')
            item['Local Price'] = local_price
        
        df = pd.DataFrame(results)
        st.table(df)
    else:
        st.write("No results found. Try a different keyword.")
else:
    st.write("Enter a keyword in the sidebar to search for bestsellers.")
