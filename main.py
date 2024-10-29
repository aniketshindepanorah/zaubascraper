from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd
import time
import json

# CSV 파일 생성 (이사회 멤버 정보 저장용)
csv_file = 'director_information.csv'
columns = ['Director Name', 'Company Name', 'CIN', 'Designation', 'Appointment Date', 'Cessation']  # 컬럼명 설정
df = pd.DataFrame(columns=columns)
df.to_csv(csv_file, index=False, encoding='utf-8-sig')  # 초기 파일 생성

# 각 회사 처리 함수 정의 (이사회 멤버 정보 추출)
def process_company(company):
    try:
        # 웹드라이버 설정 및 초기화
        service = Service(executable_path=ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(service=service, options=options)
        
        # 회사 URL로 이동
        driver.get(company['url'])
        time.sleep(10)  # Cloudflare 보호 우회를 위한 충분한 대기 시간

        # id가 'director-information-content'인 div 내의 모든 테이블 찾기
        director_info_div = driver.find_element(By.ID, 'director-information-content')
        tables = director_info_div.find_elements(By.XPATH, ".//table")

        # 추출된 데이터를 저장할 리스트
        director_data = []

        # 각 테이블 순회
        for table in tables:
            # Director Name 추출 (caption 태그에서)
            try:
                caption_text = table.find_element(By.XPATH, ".//caption").text  # caption에서 텍스트 추출
                # "Other Directorships of " 문자열을 포함하지 않으면 해당 테이블 건너뜀
                if "Other Directorships of " not in caption_text:
                    continue  # 다음 테이블로 이동
                
                # "Other Directorships of " 문자열 제거
                director_name = caption_text.replace("Other Directorships of ", "").strip()
            except:
                continue  # caption이 없는 경우 해당 테이블 건너뜀

            # 테이블의 각 행에서 데이터 추출
            rows = table.find_elements(By.XPATH, ".//tbody/tr")
            for row in rows:
                try:
                    row_data = row.find_elements(By.XPATH, ".//td")  # 'columns'를 'row_data'로 변경
                    
                    # 열의 개수가 5개 이상일 때만 처리
                    if len(row_data) >= 5:
                        company_name = row_data[0].text  # Company Name
                        cin = row_data[1].text  # CIN
                        designation = row_data[2].text  # Designation
                        appointment_date = row_data[3].text  # Appointment Date
                        cessation = row_data[4].text  # Cessation
                        
                        # 필요한 5개의 열만 추가
                        director_data.append([director_name, company_name, cin, designation, appointment_date, cessation])
                except Exception as e:
                    print(f"Error processing row: {e}")
                    continue  # 행 처리 중 문제가 발생한 경우 해당 행 건너뜀

        # 추출한 데이터를 CSV 파일에 추가
        df_new = pd.DataFrame(director_data, columns=columns)
        df_new.to_csv(csv_file, mode='a', header=False, index=False, encoding='utf-8-sig')  # 추가 모드로 저장
        
        print(f"{company['name']} 데이터가 성공적으로 저장되었습니다.")
    
    except Exception as e:
        print(f"Error occurred for {company['name']}: {str(e)}")
    
    finally:
        # 브라우저 종료
        driver.quit()

# 각 지역의 회사 목록 추출 함수
def extract_companies(region):
    base_url = f"https://www.zaubacorp.com/company-list/company-type-PTC/status-Active/paidup-G/roc-RoC-{region}/p-{{page_length}}-company.html"
    
    # 웹드라이버 설정 및 초기화
    service = Service(executable_path=ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(service=service, options=options)
    
    # 첫 페이지로 이동하여 페이지 길이 추출
    driver.get(base_url.replace("{{page_length}}", "1"))
    time.sleep(5)  # 페이지 로딩 대기

    # 페이지 수 추출 (예: Page 1 of 29)
    pagination_text = driver.find_element(By.XPATH, "//div[contains(text(), 'Companies Found')]").text
    total_pages = int(pagination_text.split("Page 1 of ")[-1].strip().split()[0])  # 총 페이지 수 추출

    # 회사 정보 저장용 리스트
    company_list = []

    # 각 페이지에서 회사 이름과 URL 추출
    for page in range(1, total_pages + 1):
        driver.get(base_url.replace("{{page_length}}", str(page)))
        time.sleep(5)  # 페이지 로딩 대기
        
        # 테이블의 각 행에서 회사명과 URL 추출
        rows = driver.find_elements(By.XPATH, "//table[@id='table']/tbody/tr")
        for row in rows:
            try:
                company_td = row.find_element(By.XPATH, "./td[2]/a")
                company_name = company_td.text  # 회사 이름
                company_url = company_td.get_attribute('href')  # 회사 URL
                
                company_list.append({
                    "name": company_name,
                    "url": company_url
                })
            except Exception as e:
                print(f"Error extracting company info on page {page}: {e}")
                continue

    driver.quit()
    return company_list

# 각 지역별 회사 목록 추출 및 저장
regions = ["Delhi", "Mumbai", "Pune"]
all_companies = []

for region in regions:
    print(f"Extracting companies for region: {region}")
    companies = extract_companies(region)
    all_companies.extend(companies)

# JSON 형식으로 저장
with open('companies.json', 'w', encoding='utf-8') as json_file:
    json.dump(all_companies, json_file, ensure_ascii=False, indent=4)

print("All company data extracted and saved in 'companies.json'.")

# 저장된 회사 정보를 바탕으로 이사회 멤버 정보 크롤링
for company in all_companies:
    process_company(company)
