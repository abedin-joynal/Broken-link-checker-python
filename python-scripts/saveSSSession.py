#!/usr/bin/python
#-*-coding:utf-8-*-
import sys
import pymysql
# from pwdVault import *
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import DesiredCapabilities
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import platform
from time import sleep, strftime
import json
from requests import session
import os

userAgentString = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36"
def getConnection(host, user, password, database, table):
    MYSQL = {}
    CONFIG = {
        'FILE'  : {
            'BASE'  : "config.base",
            'MYSQL' : "config.mysql.test",
            'RAW'   : "trbs.txt"
        },

        'BASE'  : {},
        'MYSQL' : {},
        'RAW'   : {}
        }
    CONFIG['MYSQL']['host'] = host
    CONFIG['MYSQL']['user'] = user
    CONFIG['MYSQL']['password'] = password
    CONFIG['MYSQL']['database'] = database
    tbl_name = table
    
    try:
        MYSQL['connection'] = pymysql.connect( host  =CONFIG['MYSQL']['host'],
                                            user  =CONFIG['MYSQL']['user'],
                                            passwd=CONFIG['MYSQL']['password'],
                                            db    =CONFIG['MYSQL']['database'],
                                            cursorclass=pymysql.cursors.DictCursor)
        print ("[INFO] MYSQL : Connect host =", CONFIG['MYSQL']['host'], ", database =", CONFIG['MYSQL']['database'])
    except pymysql.Error as e:
        print (e)
        return None
    return MYSQL['connection']

def getCookies(account):
    # tbl_name = 'wp_site_session'
    # db_name = 'wp_aitest'
    # host = '127.0.0.1'
    # conn = getConnection(host, DB_USER, DB_PASSWORD, db_name, tbl_name)
    sc = SessionClass()
    cursor = sc.cursor
    if not cursor:
        print('[ERROR] Cannot create session for {} account'.format(account))
    cookies = []
    try:
        sql="select * from {} where DATE=CURDATE() AND account='{}'".format(sc.tbl_name, account)
        #print sql
        result=cursor.execute(sql)
        if(result>0):
            row = cursor.fetchone()
            # print(row)
            cookies = json.loads(row['session'])
            # print(cookies)
    except pymysql.Error as e:
        print (e)
    return cookies

class SessionClass:
    def __init__(self):
        self.db_host = '127.0.0.1'
        self.db_user = os.environ['db_user']
        self.db_password = os.environ['db_password']
        self.database = os.environ['db_name']
        self.secret_key = os.environ['secret_key']
        self.tbl_name = "wp_site_session"
        self.conn = getConnection(self.db_host, self.db_user, self.db_password, self.database, self.tbl_name)
        self.cursor = self.conn.cursor()
        if not self.cursor:
            sys.exit(1)
        
        TABLES = {}
        TABLES[self.tbl_name]=("CREATE TABLE %s ("
                        " `id` int(11) NOT NULL AUTO_INCREMENT,"
                        " `date` date DEFAULT NULL,"
                        " `account` varchar(255) DEFAULT NULL,"
                        " `session` text DEFAULT NULL,"
                        " PRIMARY KEY (`id`)"
                        ")" % (self.tbl_name))
        try:
            self.cursor.execute(TABLES[self.tbl_name])
        except pymysql.Error as e:
            print (e)
        
        self.authDict={}
        
        
    def getAuthInfo(self):
        tbl_name = 'wp_account_pwd'
        conn = getConnection(self.db_host, self.db_user, self.db_password, self.database, tbl_name)
        cursor = conn.cursor()
        if not cursor:
            sys.exit(1)
        try:
            sql="select user, aes_decrypt(password, '{}') as password, account from {}".format(self.secret_key, tbl_name)
            # sql="select * from {}".format(tbl_name)
            #print sql
            result=cursor.execute(sql)
            if(result>0):
                rows = cursor.fetchall()
                for row in rows:
                    self.authDict[row['account']] = row
                    self.authDict[row['account']]['password'] = self.authDict[row['account']]['password'].decode('utf-8')
               
        except pymysql.Error as e:
            print (e)


    def getSeleniumDriver(self, URL):
        options = Options()
        if 'Windows' in platform.platform():
            options.binary_location = "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"
        # options.add_argument('--start-fullscreen')
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')

        capabilities = DesiredCapabilities.CHROME.copy()
        capabilities['acceptSslCerts'] = True 
        capabilities['acceptInsecureCerts'] = True
        tryCount=0
        while tryCount < 3:
            try:
                if 'Windows' in platform.platform():
                    driver = webdriver.Chrome(executable_path="chromedriver.exe", chrome_options=options)
                elif 'Linux' in platform.platform():
                    driver = webdriver.Chrome(executable_path='/usr/bin/chromedriver', chrome_options=options, desired_capabilities=capabilities)
                driver.set_page_load_timeout(60)
                sleep(5.0)
                driver.get(URL)
                sleep(10.0)
                return driver
                # break
            except (WebDriverException, ConnectionResetError) as e:
                print(str(e))
                try:
                    driver.close()
                except:
                    pass
                sleep(5.0)
                tryCount+=1
            finally:
                if tryCount>=3:
                    sys.exit(1)
    
    def insertData(self, account, cookies):
        DATA = {}
        placeholders = json.dumps(cookies)
        # print(placeholders)
        DATA[self.tbl_name]="INSERT INTO {} (date, account, session) VALUES ('{}', '{}', '{}')".format(self.tbl_name, strftime('%Y-%m-%d'), account, placeholders)
        # print(DATA[tbl_name])
        # sys.exit()
        try:
            self.cursor.execute(DATA[self.tbl_name])
            self.conn.commit()
            print ("[INFO] MYSQL : Session INSERTed to", self.tbl_name)
        except pymysql.Error as e:
            print (e)
    
    def updateAuthInfo(self, account, data):
        tbl_name = 'wp_account_pwd'
        conn = getConnection(self.db_host, self.db_user, self.db_password, self.database, tbl_name)
        cursor = conn.cursor()
        if not cursor:
            sys.exit(1)
        try:
            sql="UPDATE {} SET password=aes_encrypt('{}', '{}') where account='{}'".format(tbl_name, data, self.secret_key, account)
            # sql="select * from {}".format(tbl_name)
            # print (sql)
            cursor.execute(sql)
            conn.commit()
            print ("[INFO] MYSQL : AuthInfo UPDATEd to", tbl_name)
        except pymysql.Error as e:
            print (e)


    def saveSSSession(self):
        URL = 'https://smartthings.developer.SS.com/login?redirectURL=/'
        driver = self.getSeleniumDriver(URL)
        SS_USER = self.authDict['SS']['user']
        SS_PASSWORD = self.authDict['SS']['password']
        # sys.exit(0)
        elem_login = driver.find_element_by_id("iptLgnPlnID")
        elem_login.send_keys(SS_USER)
        sleep(1.5)
        elem_login = driver.find_element_by_id("iptLgnPlnPD")
        elem_login.send_keys(SS_PASSWORD)
        sleep(3.0)

        elem_login = driver.find_element_by_id("signInButton").click()
        sleep(10.0)

        cookies = driver.get_cookies()
        driver.close()
        self.insertData('SS', cookies)

    def saveCodeSession(self):
        URL = 'https://github.sec.SS.net/login'
        driver = self.getSeleniumDriver(URL)
        CODE_USER = self.authDict['code']['user']
        CODE_PASSWORD = self.authDict['code']['password']
        elem_login = driver.find_element_by_id("login_field")
        elem_login.send_keys(CODE_USER)
        sleep(1.5)
        elem_login = driver.find_element_by_id("password")
        elem_login.send_keys(CODE_PASSWORD)
        sleep(3.0)
        elem_login = driver.find_element_by_name("commit").click()
        sleep(10.0)

        cookies = driver.get_cookies()
        driver.close()
        self.insertData('code', cookies)
    
    def saveGitSession(self):
        URL = 'https://github.com/login'
        driver = self.getSeleniumDriver(URL)
        GIT_USER = self.authDict['git']['user']
        GIT_PASSWORD = self.authDict['git']['password']
        elem_login = driver.find_element_by_id("login_field")
        elem_login.send_keys(GIT_USER)
        sleep(1.5)
        elem_login = driver.find_element_by_id("password")
        elem_login.send_keys(GIT_PASSWORD)
        sleep(3.0)
        elem_login = driver.find_element_by_name("commit").click()
        sleep(10.0)

        cookies = driver.get_cookies()
        driver.close()
        self.insertData('git', cookies)
    
    def saveTizenSession(self):
        URL = 'https://www.tizen.org/user/login'
        driver = self.getSeleniumDriver(URL)
        TIZEN_USER = self.authDict['tizen']['user']
        TIZEN_PASSWORD = self.authDict['tizen']['password']
        elem_login = driver.find_element_by_id("edit-name")
        elem_login.send_keys(TIZEN_USER)
        sleep(1.5)
        elem_login = driver.find_element_by_id("edit-pass")
        elem_login.send_keys(TIZEN_PASSWORD)
        sleep(3.0)
        elem_login = driver.find_element_by_id("edit-submit").click()
        sleep(10.0)

        cookies = driver.get_cookies()
        driver.close()
        self.insertData('tizen', cookies)
    
    def saveKnoxSession(self):
        URL = 'http://SS.net/portal/default.jsp'
        driver = self.getSeleniumDriver(URL)
        KNOX_USER = self.authDict['knox']['user']
        KNOX_PASSWORD = self.authDict['knox']['password']
        elem_login = driver.find_element_by_id("USERID")
        elem_login.send_keys(KNOX_USER)
        sleep(1.5)
        elem_login = driver.find_element_by_id("USERPASSWORD")
        elem_login.send_keys(KNOX_PASSWORD)
        sleep(3.0)
        elem_login = driver.find_element_by_id("signIn").click()
        sleep(10.0)
        try:
            cur_pwd = driver.find_element_by_id('currPassword')
            cur_pwd.send_keys(KNOX_PASSWORD)
            new_pwd = driver.find_element_by_id('newPassword')
            new_pwd.send_keys(KNOX_PASSWORD[::-1])
            new_pwd = driver.find_element_by_id('confirmPassword')
            new_pwd.send_keys(KNOX_PASSWORD[::-1])
            driver.find_elements_by_class_name("pwd_change")[0].click()
            sleep(10.0)
            self.updateAuthInfo('knox', KNOX_PASSWORD[::-1])
        except Exception as e:
            print(str(e))
        try:
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "photo_img")))
            print("Knox login successful {}".format(strftime('%Y-%m-%d')))
            sleep(5.0)
            driver.get('http://www.SS.net/portal/default.jsp?mode=logout')
            sleep(5.0)
        except Exception as e:
            print(str(e))
        finally:
            driver.close()


        

if __name__ == "__main__":   
    sc = SessionClass()
    sc.getAuthInfo()
    sc.saveSSSession()
    sc.saveCodeSession()
    sc.saveGitSession()
    sc.saveTizenSession()
    sc.saveKnoxSession()