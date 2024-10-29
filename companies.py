# 필요한 라이브러리 불러오기
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import json
import time

# Base URL 정의
base_url = "https://www.zaubacorp.com/company-list/company-type-PTC/status-Active/paidup-G/roc-RoC-{{Region}}/p-{{page_length}}-company.html"

# 지역 리스트 정의
regions = ["Delhi", "Mumbai", "Pune"]

# 페이지에서 회사 정보를 추출하는 함수
def get_companies_from_page(driver, region, page_num):
    # 페이지 URL 생성
    url = base_url.replace("{{Region}}", region).replace("{{page_length}}", str(page_num))
    driver.get(url)
    time.sleep(5)  # 페이지 로딩 대기
    
    # 회사 이름과 URL을 저장할 리스트
    companies = []
    
    # 테이블에서 회사 이름과 URL 추출
    rows = driver.find_elements(By.XPATH, "//table[@id='table']/tbody/tr")
    for row in rows:
        try:
            # 두 번째 td 태그에서 회사명과 URL 추출
            company_td = row.find_element(By.XPATH, "./td[2]/a")
            company_name = company_td.text  # 회사 이름
            company_url = company_td.get_attribute('href')  # 회사 URL
            
            # 회사 정보 저장
            companies.append({"name": company_name, "url": company_url})
        except:
            continue  # 오류 발생 시 해당 회사를 건너뜀
            
    return companies

# 페이지 수를 추출하는 함수
def get_total_pages(driver, region):
    # 첫 번째 페이지 URL 생성
    first_page_url = base_url.replace("{{Region}}", region).replace("{{page_length}}", "1")
    driver.get(first_page_url)
    time.sleep(5)  # 페이지 로딩 대기

    # 페이지 수가 있는 <div> 태그 추출
    try:
        pagination_div = driver.find_element(By.XPATH, "//div[contains(text(), 'Companies Found')]")
        pagination_text = pagination_div.text
        # "Page 1 of 29"에서 마지막 숫자 추출
        total_pages = int(pagination_text.split("Page 1 of ")[1].split()[0])
        return total_pages
    except Exception as e:
        print(f"Error occurred while getting total pages for {region}: {e}")
        return 0  # 페이지 수 추출 실패 시 0 반환

# 브라우저 초기화 함수
def initialize_browser():
    service = Service(executable_path=ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# 각 지역의 모든 페이지에서 회사 정보를 추출하여 JSON 파일로 저장하는 함수
def extract_companies_from_regions():
    all_companies = []  # 모든 회사 정보를 저장할 리스트

    # 각 지역별로 회사 정보 추출
    for region in regions:
        print(f"Processing region: {region}")
        driver = initialize_browser()  # 브라우저 시작
        
        # 페이지 수 가져오기
        total_pages = get_total_pages(driver, region)
        print(f"Total pages for {region}: {total_pages}")
        
        # 각 페이지별로 회사 정보 추출
        for page_num in range(1, total_pages + 1):
            print(f"Processing page {page_num} of {region}")
            companies = get_companies_from_page(driver, region, page_num)
            all_companies.extend(companies)
            print(f"Extracted {len(companies)} companies from page {page_num} of {region}")

            # 브라우저 재시작
            driver.quit()
            driver = initialize_browser()  # 브라우저 재시작
            
        driver.quit()  # 지역별 작업 완료 후 브라우저 종료

    # 회사 정보를 JSON 파일로 저장
    with open('companies.json', 'w', encoding='utf-8') as f:
        json.dump(all_companies, f, ensure_ascii=False, indent=4)

    print(f"Total companies extracted: {len(all_companies)}")

# 회사 정보 추출 및 저장 실행
extract_companies_from_regions()
