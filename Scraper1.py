import datetime
import string
import time
from timeit import default_timer as timer

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

DEBUG = False


def atc():
    ATCrefDict = {}
    ATCinfo = []
    # Configure chrome in detach mode to persist chrome window
    chromeOptions = Options()
    chromeOptions.add_experimental_option("detach", True)
    driver = webdriver.Chrome(executable_path='./webdrivers/chromedriver', options=chromeOptions)

    # Insert loop for searching with all alphabets here
    for letter in ['B']:
        alphabet = letter
        driver.get('https://www.whocc.no/atc_ddd_index/')
        searchBox = driver.find_element_by_xpath('//*[@id="content"]/form/table/tbody/tr/td[1]/input')
        searchBox.send_keys(alphabet)
        driver.find_element_by_class_name('button').click()
        try:
            # First level Scraping
            text = driver.find_element_by_id('content').text.split('\n')

            # Removing unnecessary rows
            del text[0:2]
            del text[-1]
            firstCodes = [item[0:3] for item in text]

            # Updating Level 1 code & meaning in dictionary: ATCrefDict
            ATCrefDict = {item[0:3]: item[4:].strip() for item in text}

            # Logging
            print('First Level: ', len(firstCodes), firstCodes, '\n') if DEBUG == True else None
            for counter1 in firstCodes:
                driver.get('https://www.whocc.no/atc_ddd_index/' + '?code=' + counter1)

                # Second level Scraping
                text2 = driver.find_element_by_id('content').text.split('\n')

                # Removing unnecessary rows
                del text2[0:2]
                del text2[-1]
                del text2[0]
                secondCodes = [item.split(' ')[0] for item in text2]

                # Updating Level 2 code & meaning in dictionary: ATCrefDict
                ATCrefDict = {**ATCrefDict, **{item.split(' ')[0]: item[item.index(' ') + 1:] for item in text2}}

                # Logging
                print('Second Level: ', len(secondCodes), secondCodes, '\n') if DEBUG == True else None
                for counter2 in secondCodes:
                    driver.get('https://www.whocc.no/atc_ddd_index/' + '?code=' + counter2)

                    # Third level Scraping
                    text3 = driver.find_element_by_id('content').text.split('\n')

                    # Removing unnecessary rows
                    del text3[0:3]
                    del text3[-1]
                    del text3[0]
                    thirdCodes = [item.split(' ')[0] for item in text3]

                    # Updating Level 3 code & meaning in dictionary: ATCrefDict
                    ATCrefDict = {**ATCrefDict, **{item.split(' ')[0]: item[item.index(' ') + 1:] for item in text3}}

                    # Logging
                    print('Third Level: ', len(thirdCodes), thirdCodes, '\n') if DEBUG == True else None
                    for counter3 in thirdCodes:
                        driver.get('https://www.whocc.no/atc_ddd_index/' + '?code=' + counter3)

                        # Issue01 | Flag setting
                        Issue01 = False

                        # Fourth level Scraping
                        text4 = []
                        if driver.page_source.__contains__('<td>Adm.R</td>'):
                            tableBody = driver.find_element_by_xpath('//*[@id="content"]/ul/table/tbody')
                            rowOfDetails = tableBody.find_elements_by_tag_name('tr')
                            c1 = c2 = iv1 = iv2 = 0
                            # Issue01 | Special case: subcategory has no code or name - Inheriting the previous level
                            if rowOfDetails[0].text.split('  ')[0] == 'ATC code' and \
                                    len(rowOfDetails[1].text.split('  ')[0]) != 7:
                                iv1 = counter3 + '**'
                                iv2 = ATCrefDict[counter3].strip()
                                Issue01 = True
                            # Normal case - every detail present in the table
                            for element in rowOfDetails:
                                tempRow = [item.strip() for item in element.text.split('  ')]
                                print(len(tempRow), tempRow) if DEBUG == True else None
                                # Swapping & shifting logic
                                if len(tempRow) >= 5:
                                    c1, c2 = tempRow[0:2]
                                if len(tempRow) == 3:
                                    a, b, c = tempRow[0:3]
                                    tempRow = [c1, c2, a, b, c]
                                    if Issue01:
                                        tempRow = [iv1, iv2, a, b, c]
                                if len(tempRow) == 4:
                                    a, b, c, d = tempRow[0:4]
                                    tempRow = [c1, c2, a, b, c, d]
                                    if Issue01:
                                        tempRow = [iv1, iv2, a, b, c, d]
                                print(tempRow)
                                text4.append(tempRow) if 'ATC c' not in element.text else None
                                # Logging
                                print(text4) if DEBUG == True else None
                            # Storing data
                            ATCinfo.append(text4)
                        else:
                            pass
        except(Exception):
            print('Error in ', letter, ', No data found') if DEBUG == True else None
    driver.close()
    # Congregating
    ATCinfo = [item for sublist in ATCinfo for item in sublist]
    return [ATCinfo, ATCrefDict]


def fda():
    FDAinfo = []
    chromeOptions = Options()
    chromeOptions.add_experimental_option("detach", True)
    driver = webdriver.Chrome(executable_path='./webdrivers/chromedriver', options=chromeOptions)
    for letter in string.ascii_uppercase:
        level = []
        driver.get('https://www.accessdata.fda.gov/scripts/cder/daf')
        driver.find_element_by_link_text(letter).click()
        numPages = driver.find_element_by_class_name('pagination').text.split('\n')[2:-2]
        for page in numPages:
            driver.find_element_by_link_text(page).click()
            level.append(driver.find_element_by_css_selector(
                '#mp-pusher > div > div > div > div > div.row.content > div > table > tbody').text.split('\n'))
        level = [item for sublist in level for item in sublist]
        # The list Level now contains every drug name with current letter eg: 'A'
        for drug in level:
            # Search for specific drug from level list
            driver.get('https://www.accessdata.fda.gov/scripts/cder/daf')
            search = driver.find_element_by_id('searchterm')
            search.send_keys(drug)
            driver.find_element_by_css_selector('#DrugNameform > div:nth-child(2) > button:nth-child(1)').click()
            time.sleep(1)

            # View results - can be segregated into specific product search outcome, eg: AUGMENTIN '875'
            # Or A-HYDROCORT searches which list down a number of combinations.
            if 'Marketing' in driver.page_source:
                # Directly extracting information from target page
                FDAinfo.append(driver.find_element_by_xpath('//*[@id="exampleProd"]/tbody').text)
            else:
                # Iterating through each of the subcategories and opening one-by-one to extract information
                driver.find_element_by_link_text(drug).click()
                time.sleep(2)
                subcategories = len(driver.find_element_by_id('drugName1').text.split('\n'))
                for subDrugsCounter in range(1, subcategories + 1):
                    driver.get('https://www.accessdata.fda.gov/scripts/cder/daf')
                    search = driver.find_element_by_id('searchterm')
                    search.send_keys(drug)
                    driver.find_element_by_css_selector(
                        '#DrugNameform > div:nth-child(2) > button:nth-child(1)').click()
                    driver.find_element_by_link_text(drug).click()
                    time.sleep(2)
                    driver.find_element_by_xpath('//*[@id="drugName1"]/li[' + str(subDrugsCounter) + ']/a').click()
                    FDAinfo.append(driver.find_element_by_xpath('//*[@id="exampleProd"]/tbody').text.split('\n'))
            # Logging for error checking
            print(drug, FDAinfo, '\n') if DEBUG == True else None
    driver.close()
    return FDAinfo


def drugs():
    drugsInfo = []
    drugIndexLinks = []
    drugView = []
    chromeOptions = Options()
    chromeOptions.add_experimental_option("detach", True)
    driver = webdriver.Chrome(executable_path='./webdrivers/chromedriver', options=chromeOptions)
    # Loop to find all drug names as per indexed pages
    for letter in string.ascii_lowercase:
        driver.get('https://www.drugs.com/alpha/' + letter + '.html')
        # Trying to find active html references for redirection
        topList = driver.find_element_by_class_name('ddc-paging')
        links = [item.get_attribute('href') for item in topList.find_elements_by_tag_name('a')]
        print(links) if DEBUG == True else None
        drugIndexLinks.append(links)

    # Now the list: drugIndexLinks has all the available link combinations, we can access them directly and extract data
    drugIndexLinks = [item for sublist in drugIndexLinks for item in sublist]

    for link in drugIndexLinks:
        driver.get(link)
        drugTable = driver.find_element_by_css_selector('#content > div.contentBox > ul')
        eachDrugLink = [item.get_attribute('href') for item in drugTable.find_elements_by_tag_name('a')]
        print(eachDrugLink) if DEBUG == True else None
        drugView.append(eachDrugLink)

    # Now the list: drugView has all the drug page links
    drugView = [item for sublist in drugView for item in sublist]

    for link in drugView:
        driver.get(link)
        try:
            # Pronunciation Available
            name = driver.find_element_by_class_name('pronounce-title').text
        except Exception:
            # Pronunciation Unavailable
            name = driver.find_element_by_css_selector('#content > div.contentBox > h1').text
        try:
            # Subtitle available having brand name and information
            text = driver.find_element_by_class_name('drug-subtitle').text.split('\n')
        except Exception:
            # Information Unavailable, leaving it as blank
            text = []
        drugsInfo.append([name, text])
    return drugsInfo


def chembl():  # Take multiple CHEMBL compounds with similar names
    chromeOptions = Options()
    chromeOptions.add_experimental_option("detach", True)
    driver = webdriver.Chrome(executable_path='./webdrivers/chromedriver', options=chromeOptions)
    wait = WebDriverWait(driver, 200)
    driver.get('https://www.ebi.ac.uk/chembl/')
    time.sleep(2)
    driver.find_element_by_id('keyword').clear()
    searchBox = driver.find_element_by_id('keyword')
    searchBox.send_keys('A-HYDROCORT')
    driver.find_element_by_css_selector('#compound_button > span > span > span:nth-child(1)').click()
    try:
        wait.until(expected_conditions.visibility_of_element_located((By.ID, 'bodyHeaderTitle')))
        if '0 Hits' in driver.find_element_by_id('bodyHeaderTitle').text:
            print('No result found for the compound:') if DEBUG == True else None
        else:
            time.sleep(2)
            table = driver.find_element_by_id('example')
            linksToChemical = [item.get_attribute('href') for item in table.find_elements_by_tag_name('a')]
            print(linksToChemical) if DEBUG == True else None
            for link in linksToChemical:
                driver.get(link)
                print(driver.find_element_by_class_name('contenttable_lmenu').text)
    except Exception:
        print('Page loading issue') if DEBUG == True else None


def findATC_Levels_123(fourthLevelCode, ATC_Level_Dict):
    newATCDict = {}
    for key, value in ATC_Level_Dict.items():
        newATCDict[key] = value.replace(',', ' &')
    print(newATCDict) if DEBUG == True else None
    tempLevelString = []
    for key, value in newATCDict.items():
        if fourthLevelCode.startswith(key):
            tempLevelString.append(key)
            tempLevelString.append(value)
    print(len(tempLevelString), tempLevelString) if DEBUG == True else None
    return tempLevelString


if __name__ == '__main__':
    #########################
    # ATC Report Generation #
    #########################
    startTime = timer()
    ATClevel4array, ATC_Level_Dict = atc()
    # print(ATClevel4array)
    ATC_DataFrame = pd.DataFrame.from_records(ATClevel4array, columns=['ATC_Code', 'Name', 'DDD', 'U', 'Adm.R', 'Note'])
    ATC_DataFrame['L1_Code'] = ATC_DataFrame['ATC_Code'].apply(lambda x: findATC_Levels_123(x, ATC_Level_Dict)[0])
    ATC_DataFrame['L1_Name'] = ATC_DataFrame['ATC_Code'].apply(lambda x: findATC_Levels_123(x, ATC_Level_Dict)[1])
    ATC_DataFrame['L2_Code'] = ATC_DataFrame['ATC_Code'].apply(lambda x: findATC_Levels_123(x, ATC_Level_Dict)[2])
    ATC_DataFrame['L2_Name'] = ATC_DataFrame['ATC_Code'].apply(lambda x: findATC_Levels_123(x, ATC_Level_Dict)[3])
    ATC_DataFrame['L3_Code'] = ATC_DataFrame['ATC_Code'].apply(lambda x: findATC_Levels_123(x, ATC_Level_Dict)[4])
    ATC_DataFrame['L3_Name'] = ATC_DataFrame['ATC_Code'].apply(lambda x: findATC_Levels_123(x, ATC_Level_Dict)[5])
    ATC_DataFrame = ATC_DataFrame[
        ['L1_Code', 'L1_Name', 'L2_Code', 'L2_Name', 'L3_Code', 'L3_Name', 'ATC_Code', 'Name', 'DDD', 'U', 'Adm.R',
         'Note']]
    ATC_DataFrame.to_csv('ATC Dump ' + str(datetime.datetime.now().strftime('%Y-%m-%d')) + '.csv', index=None)
    print('ATC Dump generated in {} seconds'.format(timer() - startTime))
