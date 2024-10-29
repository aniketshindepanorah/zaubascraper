# Import necessary libraries
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd
import time
import json

# Create CSV file (create file on first run)
csv_file = 'director_information.csv'
columns = ['Director Name', 'Company Name', 'CIN', 'Designation', 'Appointment Date', 'Cessation']  # Set column names
df = pd.DataFrame(columns=columns)
df.to_csv(csv_file, index=False, encoding='utf-8-sig')  # Create initial file

# Define function to process each company
def process_company(company):
    try:
        # Set up and initialize web driver
        service = Service(executable_path=ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(service=service, options=options)
        
        # Navigate to company URL
        driver.get(company['url'])
        time.sleep(10)  # Sufficient wait time to bypass Cloudflare protection

        # Find all tables within the div with id 'director-information-content'
        director_info_div = driver.find_element(By.ID, 'director-information-content')
        tables = director_info_div.find_elements(By.XPATH, ".//table")

        # List to store extracted data
        director_data = []

        # Iterate through each table
        for table in tables:
            # Extract Director Name (from caption tag)
            try:
                caption_text = table.find_element(By.XPATH, ".//caption").text  # Extract text from caption
                print(caption_text)
                # Skip table if it does not contain the string "Other Directorships of "
                # if "Other Directorships of " not in caption_text:
                #     print("Caption does not match. Skipping table.")
                #     continue  # Move to the next table
                print(caption_text.count("Other"))
                if caption_text.count("Other") == 0:
                    print("No captions found. Skipping table.")
                    continue
                # Remove the string "Other Directorships of "
                director_name = caption_text.replace("Other Directorships of ", "").strip()
                print(f"Director Name: {director_name}")
            except:
                print("Table does not have a caption. Skipping table.")
                continue  # Skip table if it does not have a caption

            # Extract data from each row in the table
            rows = table.find_elements(By.XPATH, ".//tbody/tr")
            for row in rows:
                try:
                    row_data = row.find_elements(By.XPATH, ".//td")  # Change 'columns' to 'row_data'
                    
                    # Process only if there are at least 5 columns
                    if len(row_data) >= 5:
                        print(f"Row data: {row_data}")
                        company_name = row_data[0].text  # Company Name
                        cin = row_data[1].text  # CIN
                        designation = row_data[2].text  # Designation
                        appointment_date = row_data[3].text  # Appointment Date
                        cessation = row_data[4].text  # Cessation
                        
                        # Add only the required 5 columns
                        director_data.append([director_name, company_name, cin, designation, appointment_date, cessation])
                except Exception as e:
                    print(f"Error processing row: {e}")
                    continue  # Skip row if there is an issue processing it

        # Append extracted data to CSV file
        print(f"Director data: {director_data}")
        df_new = pd.DataFrame(director_data, columns=columns)
        df_new.to_csv(csv_file, mode='a', header=False, index=False, encoding='utf-8-sig')  # Save in append mode
        
        print(f"Data for {company['name']} has been successfully saved.")
    
    except Exception as e:
        print(f"Error occurred for {company['name']}: {str(e)}")
    
    finally:
        # Close browser
        driver.quit()

# Array of company information (can include omitted parts)
# companies = [
#     {"name": "G D GOENKA PRIVATE LIMITED", "url": "https://www.zaubacorp.com/company/G-D-GOENKA-PRIVATE-LIMITED/U74899DL1976PTC008160"},
#    {"name": "HAWK CAPITAL PRIVATE LIMITED","url":"https://www.zaubacorp.com/company/HAWK-CAPITAL-PRIVATE-LIMITED/U74899DL1995PTC067864"},
# {"name":"POLICYBAZAAR INSURANCE BROKERS PRIVATE LIMITED","url":"https://www.zaubacorp.com/company/POLICYBAZAAR-INSURANCE-BROKERS-PRIVATE-LIMITED/U74999HR2014PTC053454"},
# {"name":"ARYAHI BUILDWELL PRIVATE LIMITED","url":"https://www.zaubacorp.com/company/ARYAHI-BUILDWELL-PRIVATE-LIMITED/U70109DL2006PTC155582"},
# ]


def load_companies_from_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        companies = json.load(f)
    return companies

companies = load_companies_from_json('companies.json')
# Iterate through each company
for company in companies:
    process_company(company)  # Process company data
