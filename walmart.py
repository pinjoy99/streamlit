import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import json
import requests

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def search_walmart(keyword, driver):
    url = f"https://www.walmart.com/search?q={keyword}&sort=best_seller"
    driver.get(url)
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-item-id]"))
    )
    
    items = driver.find_elements(By.CSS_SELECTOR, "div[data-item-id]")
    results = []
    
    for item in items[:5]:  # Limit to first 5 results for demonstration
        try:
            item_id = item.get_attribute("data-item-id")
            title = item.find_element(By.CSS_SELECTOR, 'span[data-automation-id="product-title"]').text
            price = item.find_element(By.CSS_SELECTOR, 'div[data-automation-id="product-price"]').text
            
            results.append({
                'Item': title.strip(),
                'Online Price': price.strip(),
                'Item ID': item_id
            })
        except:
            continue
    
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
    
    driver = setup_driver()
    results = search_walmart(keyword, driver)
    driver.quit()
    
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
