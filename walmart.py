import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

def search_walmart(keyword):
    url = f"https://www.walmart.com/search?q={keyword}+clearance&facet=pickup_and_delivery%3A118%20Pickup"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    items = soup.find_all('div', class_='mb1 ph1 pa0-xl bb b--near-white w-25')
    
    results = []
    for item in items[:5]:  # Limit to first 5 results for demonstration
        title = item.find('span', class_='w_DJ')
        price = item.find('div', class_='b black f5 mr1 mr2-xl lh-copy f4-l')
        availability = item.find('div', class_='f6 f5-l gray mr1 mt2 lh-title')
        
        if title and price and availability:
            results.append({
                'Item': title.text.strip(),
                'Price': price.text.strip(),
                'Availability': availability.text.strip()
            })
    
    return results

st.title("Walmart Clearance Deals Near 48864")

keyword = st.sidebar.text_input("Enter keyword for clearance deals:")

if keyword:
    st.write(f"Searching for '{keyword}' clearance deals...")
    results = search_walmart(keyword)
    
    if results:
        df = pd.DataFrame(results)
        st.table(df)
    else:
        st.write("No results found. Try a different keyword.")
else:
    st.write("Enter a keyword in the sidebar to search for clearance deals.")
  
