import re
import sys
import time
import threading
from bs4 import BeautifulSoup
from datetime import datetime
from requests import session
from urllib.parse import urlparse, urljoin, unquote
#from urllib.parse import unquote
from pandas import DataFrame
from urllib.error import URLError, HTTPError
from requests.exceptions import ConnectionError, Timeout, InvalidSchema
import argparse
import socket
from http.client import RemoteDisconnected
# from pwdVault import *
import yaml
import json
from time import sleep
from saveSSSession import getCookies
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
import platform

#http.client.HTTPConnection._http_vsn = 10
#http.client.HTTPConnection._http_vsn_str = 'HTTP/1.0'

start = time.time()
num, maxnum = 0, 0
maxthreadsnum = 15	# If the performance of your PC is low, please adjust this value to 5 or less.
maxDepth = 10000
outputFile = None
cu, du, url, prefix, path = '', '', '', '', ''
link_pt1, link_pt2 = '', ''
rdfList=[]
dfDict={}
timedOutList=[]
sess = None
tagList = []
operationList = []
sectionList = []
jsApidict = {}
userAgentString = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36"
excludedfiles = ('.ico', '.png', '.jpg', '.jpeg', '.gif', '.pdf', '.bmp', '.tif', '.svg', '.pic', \
    '.rle', '.psd', '.pdd', '.raw', '.ai', '.eps', '.iff', '.fpx', '.frm', '.pcx', '.pct', '.pxr', '.sct', \
    '.tga', '.vda', '.icb', '.vst', '.bin', '.exe', '.dmg', '.zip', '.tar.gz', '.jar')

class CustomError(Exception):
    def __init__(self, link, code):
        self.link=link
        self.code=code

def init():

    global maxthreadsnum, maxDepth, outputFile, link_pt1, link_pt2
    global cu, du, url, prefix		# cu: current URL, du: domain URL
    parser = argparse.ArgumentParser(description="Site link checker", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-T", "--target-url", help="Target URL to test")
    parser.add_argument("-b", "--git-branch", type=str, default='master', help="Git branch name\nDefault: master")
    parser.add_argument("-M", "--max-thread", type=int, default=15, help="Maximum number of threads\nDefault: 15")
    parser.add_argument("-d", "--max-depth", type=int, default=10000, help="Maximum number of depth to crawl\nDefault: 5")
    parser.add_argument("-O", "--output-file", help="Output file name")
    parser.add_argument("-L", "--log-file", help="Log file name")
    args = parser.parse_args()
    if args.target_url:
        url = str(args.target_url)
        #url = url+"/" if not url.endswith("/") else url
        up = urlparse(url)
        if all([up.scheme, up.netloc]) and up.scheme.find('http')>=0:
            prefix = up.scheme + "://"
            du = up.netloc
            cu = du + up.path
        else:
            print ('[ERR] Please be sure to include "http://" or "https://" in the target URL.')
            return False
        
        if(du.find('github')>=0):
            m = re.match(r'(.*)/(tree|blob)/(.*)', prefix + cu)
            if m:
                link_pt1 = m.group(1)
                link_pt2 = m.group(3)
            else:
                branch = '/tree/'+args.git_branch
                link_pt1 = prefix + cu
                link_pt2 = args.git_branch
                cu = cu + branch              
        
    else:
        print ('[ERR] Please input required target URL.')
        return False
    if args.max_thread:
        maxthreadsnum = int(args.max_thread)
    
    if args.max_depth:
        if (maxDepth>0):
            maxDepth = int(args.max_depth)
        else:
            maxDepth=10000
    if args.output_file:
        outputFile = args.output_file

    return True

def loginCode():
    print("+ Authenticating github.sec.SS.net")
    global userAgentString
    cookies = []
    cookies = getCookies('code')
    s=session()
    s.headers.update({'User-Agent': userAgentString})
    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])
    return s

def loginGithub():
    print("+ Authenticating github.com")
    global userAgentString
    cookies = []
    cookies = getCookies('git')
    s=session()
    s.headers.update({'User-Agent': userAgentString})
    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])
    return s

def loginTZ():
    print("+ Authenticating TZ.org")
    global userAgentString
    cookies = []
    cookies = getCookies('TZ')
    s=session()
    s.headers.update({'User-Agent': userAgentString})
    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])
    return s

def loginSS():
    print("+ Authenticating SS.com")
    global userAgentString
    cookies = []
    cookies = getCookies('SS')
    s=session()
    s.headers.update({'User-Agent': userAgentString})
    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])
    return s

# Deletion the last '/' of the target URL
def checkTail(str):
    str = str.rstrip()
    check = checkDomain(str)
    '''
    if not str.endswith("/") and check!=None: 
        token = str.split('/')[-1]
        if "." not in token and "#" not in token and check:
            str = str+"/"
    '''
    return (str, check)
special_headers = {'X-PJAX':'true', 'Content-Type': 'application/x-www-form-urlencoded', 'Accept-Charset': 'UTF-8'}

def getCode(tu, sess=None):
    global rdfList		# rdfList: List array for final result
    global start, num, cu, excludedfiles, dfDict
    global timedOutList # timedOutList: List array for timeout urls
    global special_headers
    code = ''
    status = False
    #req = None
    html = None
    visited = True
    redir_link = ""
    #redir = None
    try:
        try:
            if tu.endswith(excludedfiles):
                html = sess.head(tu, timeout=120)
            else:
                if(re.search('native-application\?redirect=', tu)):
                    sess.headers.update(special_headers)
                else:
                    try:
                        for key in special_headers.keys():
                            sess.headers.__delitem__(key)
                    except:
                        pass
                html = sess.get(tu, timeout=120)
            #if html.url.find(tu) < 0:
            code = str(html.status_code)
            if html.url != tu and not code.startswith('4'):
                code = "302"
                redir_link = html.url
                status = True if html.url.find(cu)>=0 else False
            else:
                if(code=='429'):
                    print("+ too many requests... pausing the thread")
                    try:
                        time.sleep(int(html.headers['Retry-After']))
                    except:
                        time.sleep(120)
                    raise CustomError(tu, code)
                elif not code.startswith('4'):
                    acode = checkAnchorLink(html.text, tu)
                    if(acode):
                        code = acode
                        if code == '404':
                            # print("[ERROR] <a class='view-source-link' href='#' data={}>{}</a>".format(tu[:tu.find('#')], dfDict[tu]['link']))
                            print("[ERROR] <a href=view-source:{} target='_blank_'>{}</a>".format(tu[:tu.find('#')], dfDict[tu]['link']))
                elif(code == '404'):
                    print("[ERROR] <a href={} target='_blank_'>{}</a>".format(tu, dfDict[tu]['link']))
                status = True

            print('\n[OK] The server could fulfill the request to\n%s' %tu)
            
        except HTTPError as e:
            code = str(e.code)
            print('\n[ERR] HTTP Error: The server couldn\'t fulfill the request to\n%s' %tu)
        except URLError as e:
            code = e.reason
            print('\n[ERR] URL Error: We failed to reach in\n%s\n+ %s' %(tu, code))
        except RemoteDisconnected as e:
            code=str(e)
            print('\n[ERR] Remote Disconnect Error: We failed to reach in\n%s\n+ %s' %(tu, code))
        except InvalidSchema as e:
            code=str(e)
            print('\n[ERR] Invalid Schema Error: We failed to reach in\n%s\n+ %s' %(tu, code))
        except socket.timeout as e:
            code = e.errno
            #print('\n[ERR] TIMEOUT Error: We failed to reach in\n%s\n+ %s' %(tu, code))
            raise CustomError(tu, code)
        except Timeout as e:
            code=str(e)
            raise CustomError(tu, code)
            #print('\n[ERR] Connection Error: We failed to reach in\n%s\n+ %s' %(tu, code))
        except ConnectionError as e:
            code = str(e)
            raise CustomError(tu, code)
            #print('\n[ERR] Connection Error: We failed to reach in\n%s\n+ %s' %(tu, code))
    except CustomError as e:
        if e.link not in timedOutList:
            #visited=False
            print('\n[ERR] Connection Error: We failed to reach in\n%s\n+ %s First time' %(e.link, e.code))
            timedOutList.append(e.link)
            return (status, html, False, e.code)
        else:
            print('\n[ERR] Connection Error: We failed to reach in\n%s\n+ %s Second time' %(e.link, e.code))

    parent = dfDict[tu]['parent']
    rows = [parent, tu, code, redir_link]
    rdfList.append(rows)
    counts = len(rdfList)

    end = time.time()
    cs = end - start
    cm = cs // 60
    cs = "{0:.1f}".format(cs % 60)

    if counts == 1:
        print ('+ Searching target URL: %d(min) %s(sec)' %(cm, cs))
    else:
        sv = "{0:.1f}".format((counts * 100) / num) + '%'
        print ('+ Searching %s(%d/%d, %d): %d(min) %s(sec)' %(sv, counts, num, maxnum, cm, cs))
    return (status, html, visited, code)

def checkDomain(link):
    global cu, du, prefix, link_pt1, link_pt2
    '''
    token = link.split('/')[-1]
    if "." in token and "#" not in token:
        return False
    '''
    if link.find('logout')> -1:
        return None

    if(du.find('github')>=0):
        k = re.match(link_pt1+'/(tree|blob)/'+link_pt2+'.*', link)
        if k:
            return True
        else:
            l = re.match(link_pt1+'/(tree|blob)/.*', link)
            if l:
                return None
    elif(link.find(cu)>=0):
        return True

    return False

def st_api_check(link):
    global sess, tagList, operationList, sectionList
    url = urljoin(link,'./resources/st-api.yml')
    h = sess.get(url)
    k=yaml.load(h.text)
    
    desc = k['info']['description']
    lst = desc.split('\n')
    for p in lst:
        if(p.startswith('##')):
            m = re.search('^## (.+)$', p.strip())
            sectionList.append((parent+'/'+m.group(1)).replace(' ','-'))
        elif(p.startswith('#')):
            m = re.search('^# (.+)$', p.strip())
            parent = m.group(1)
            sectionList.append(parent.replace(' ','-'))

    for l in k['paths']:
        for key in k['paths'][l]:
            if key in ['get','post','delete','put']:
                tag = k['paths'][l][key]['tags'][0]
                if tag not in tagList:
                    tagList.append(tag)
                op = k['paths'][l][key]['operationId']
                if op not in operationList:
                    operationList.append(op)

def js_api_check(link):
    global sess, jsApidict
    url = urljoin(link,'api_data.js')
    h = sess.get(url)
    json_txt=h.text[7:-2]
    regex_content = r"[\"|\']?content[\'|\"]?([\s]+)?:([\s]+)?([\'|\"])(.*?)\3,"
    json_txt = re.sub(regex_content, r'content:"",',json_txt)

    regex_optional = "[\"|\']?optional([\s]+)?:([\s]+)?(![0-9])"
    json_txt = re.sub(regex_optional, r'optional:"\3"', json_txt)

    regex_key = "([{|,])([a-zA-Z0-9]*?):"
    json_txt = re.sub(regex_key, r'\1"\2":', json_txt)
    # print(json_txt)
    k = json.loads(json_txt)

    # k=json.loads(''.join(h.text.split('\n'))[7:-2])
    for j in k['api']:
        try:
            jsApidict[j['group']].append(j['name'])
        except:
            jsApidict[j['group']] = [j['name']]
        # print('api-{}-{}'.format(j['group'],j['name']))

def checkAnchorLink(source, link):
    global tagList, operationList, sectionList
    global jsApidict 
    acode = None
    m=re.search('#(.+)$',link)
    if m:
        if link.find('/docs/api-ref/st-api.html') > -1:
            if(len(sectionList)==0 or len(operationList)==0 or len(tagList)==0):
                st_api_check(link)
            p = m.group(1).split('/', 1)
            if (((p[0] == 'section') and (p[1] in sectionList))
            or ((p[0] == 'tag') and (p[1] in tagList))
            or ((p[0] == 'operation') and (p[1] in operationList))):
                acode = '200'
            else:
                acode = '404'
            return acode
        
        elif link.find('/docs/api-ref-javadocs/jsapi_doc/index.html') > -1:
            if(len(jsApidict)==0):
                js_api_check(link)
            p = m.group(1).split('-')
            if (p[2] in jsApidict[p[1]]):
                acode = '200'
            else:
                acode = '404'
            return acode
        
        s = re.search('web-application(\?redirect=.*)',link)
        if(s):
            source = get_source_web_apireference(s.group(1))
        
        if link.find('github.com') > -1:
            id_str = re.compile(r"^{}|^{}".format('user-content-'+m.group(1),unquote(m.group(1))))
            # id_str = 'user-content-'+m.group(1)
        else:
            id_str = unquote(m.group(1))
        
        soup = BeautifulSoup(source, 'lxml')
        if(len(soup.findAll(id=id_str))==1 or m.group(1)=='#none' 
        or len(soup.findAll(True, attrs={'name':m.group(1)}))==1):
            acode = '200'
        else:
            acode = '404'
    return acode

def get_source_web_apireference(param):
    global sess
    temp_tu = 'https://developer.TZ.org/apireference/contents/18286/deflated'+param
    try:
        r=sess.get(temp_tu, timeout=120)
        page = r.json()['content']
    except:
        print("=========="+param+"===========")
        sys.exit(1)
    return page

def get_source_selenium(url):
    options = Options()
    if 'Windows' in platform.platform():
        options.binary_location = "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"
    # options.add_argument('--start-fullscreen')
    # options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    tryCount=0
    data = None
    while tryCount < 3:
        try:
            if 'Linux' in platform.platform():
                driver = webdriver.Chrome(executable_path='/usr/bin/chromedriver', chrome_options=options)
            elif 'Windows' in platform.platform():
                driver = webdriver.Chrome(executable_path="chromedriver.exe", chrome_options=options)
            #sleep(5.0)
            driver.get(url)
            sleep(10.0)
            data = driver.page_source
            # soup = BeautifulSoup(data, 'lxml')
            break
        except WebDriverException as e:
            print(str(e))
            sleep(5.0)
            tryCount+=1
        finally:
            try:
                driver.close()
            except:
                pass
            if tryCount>=3:
                print("[ERROR] Something went wrong with selenium")
                sys.exit(1)
    return data

def getLink(tu, depth, check_child):
    global dfDict, sess
    global cu, maxnum, num, maxDepth	# maxnum: maximum # of data frame
    global excludedfiles

    (status, html, visited, code) = getCode(tu, sess)

    dfDict[tu]['visited'] = visited
    
    if status == False or check_child == False:
        return False
    
    if depth+1 > maxDepth:
        return False
    
    parent = dfDict[tu]['parent']
    if code == "302":
        tu = html.url

    #print(html.read())
    tokens = tu.split('/')
    lasttoken = tokens[-1]
    #if lasttoken.find('#') >= 0 or lasttoken.find('?') >= 0 or lasttoken.find('%') >= 0 or excludedfiles.find(lasttoken[-4:]) >= 0:
    if lasttoken!="" and (lasttoken.find('?') >= 0 or lasttoken.find('#') >= 0 or lasttoken.endswith(excludedfiles)):
        print ('+ This "%s" is skipped because it`s not the target of the getLink().' %lasttoken)
        return False
    else:
        if sess:
            m = re.search('web-application(\?redirect=.*)',tu)
            if(m):
                page = get_source_web_apireference(m.group(1))
            elif re.search('/api-references/(native|web)-application$',tu):
                page = get_source_selenium(tu) 
            else:
                page = html.text
        else:
            page = html.read().decode("utf-8",'ignore')
        try:
            soup = BeautifulSoup(page, 'lxml')
            #print(soup)
        except Exception as e:
            print("======"+tu+"======")
            print(str(e))
            return False
        result = soup.find("meta",attrs={"http-equiv":"refresh"})
        #print(result)
        if result:
            redir_link = None
            #b'<meta http-equiv="refresh" content="0; url=./overview" />'
            m = re.match('.*url=(.*).*',result.get('content'))
            if m:
                '''
                if not tu.endswith("/"):
                    redir_link = urljoin(tu+"/", m.group(1))
                else:
                '''
                redir_link = urljoin(tu, m.group(1))
                #print ("=====>>>>>>>>>>"+redir_link)
                (redir_link, check_child) = checkTail(redir_link)
                if redir_link != tu and check_child!=None:
                    maxnum = maxnum + 1
                    if redir_link not in dfDict:
                        dfDict[redir_link]={'parent':parent,'visited': False, 'depth': depth, 'check': check_child}
                        num = num + 1

        for link in soup.findAll('a', attrs={'href': re.compile('^http|^/|^\.|^[A-z]|^\?redirect')}):
            nl = link.get('href')	# nl: new link
            if (nl.find('mailto:') > -1):
                continue
            
            if nl.startswith("/"):
                nl = urljoin(tu, nl)
            elif nl.startswith("?redirect"):
                # print(nl)
                m = re.search('/api-references/(native|web)-application', tu)
                if (m):
                    if ((m.group(1)=='web' and (nl.find('org.TZ.web.apireference') > -1)) 
                    or (m.group(1)=='native' and re.search('org\.TZ\.native\..+\.apireference', nl))):
                        nl = urljoin(tu, nl)
                    else:
                        continue
            elif not nl.startswith("http"):
                nl = urljoin(tu, nl)
            (nl, check_child) = checkTail(nl)
            if nl != tu and check_child!=None:
                maxnum = maxnum + 1
                if nl not in dfDict:
                    m = re.search(url+'(.*)$', nl)
                    if m:
                        link_leveled = m.group(1)
                    else:
                        link_leveled = link.get('href')
                    dfDict[nl]={'parent':tu,'visited': False, 'depth': depth+1, 'check': check_child, 'link': link_leveled}
                    #dfDict[nl]={'parent':parent,'visited': visited, 'depth': depth, 'check': check_child}
                    num = num + 1
                    #print ('+ Adding rows(%d):\n%s'%(num, rows))
        return True

def runMultithread(tu):

    global maxthreadsnum, dfDict, num, sess, timedOutList
    threadsnum = 0

    if len(dfDict) == 0:
        dfDict[tu]={'parent':"",'visited': False, 'depth': 0, 'check': True}
        num += 1
        if tu.find('github.sec.SS.net') > 0:
            sess = loginCode()
        elif tu.find('github.com') > 0:
            sess = loginGithub()
        elif tu.find('TZ.org') > 0:
            sess = loginTZ()
        elif tu.find('SS.com') > 0:
            sess = loginSS()
        else:
            sess = session()
            sess.headers.update({'User-Agent': userAgentString})
        print ('First running with getLink()')

    threads = [threading.Thread(target=getLink, args=(durl, dfDict[durl]['depth'], dfDict[durl]['check'])) for durl in dfDict if dfDict[durl]['visited']==False]
    for thread in threads:
        threadsnum = threading.active_count()
        while threadsnum > maxthreadsnum:
            time.sleep(0.5)
            threadsnum = threading.active_count()
            print ('+ Waiting 0.5 seconds to prevent threading overflow.')
        try:
            thread.daemon = True
            thread.start()
        except:
            print ('[ERR] Caught an exception of "thread.start()".')
    for thread in threads:
        try:
            thread.join()
        except:
            print ('[ERR] Caught an exception of "thread.join()".')


def result(tu, cm, cs):

    global path, num, rdfList, outputFile, timedOutList

    rdf = DataFrame(rdfList, columns=['parent','link','code','redirect to']) # rdf: data frame for final result
    rdf.sort_values(by=['parent', 'link'], ascending=[True,True], inplace=True)
    #print ("Before duplicates checking: "+str(len(rdf)))
    #rdf.drop_duplicates(subset='link', inplace=True, keep='first')
    #print ("after duplicates checking: "+str(len(rdf)))
    rdf.index = range(len(rdf))
    count = num
    num = len(rdf)
    print ('+ updating the total number of links from %d to %d' %(count, num))

    print ('[OK] Result')

    print ('[OK] Total number of broken link is %d' %(len(rdf.loc[rdf['code']=='404'])))

    target = tu.replace('://','_').replace('/','_')
    path = datetime.now().strftime('%Y-%m-%d_%H-%M_')
    path = path + '_' + cm + '(min)' + cs + '(sec)_' + target + '.csv'
    rdf.to_csv(outputFile, header=True, index=True)
    #rdf.to_csv(path, header=True, index=True)

    return len(rdf)

if __name__ == "__main__":

    if init():
        while len(dfDict) == 0 or len(rdfList)<len(dfDict):
            runMultithread(url)
        end = time.time()
        cs = end - start
        cm = str(int(cs // 60))
        cs = "{0:.1f}".format(cs % 60)
        dnum = result(url, cm, cs)
        print ('\n[OK] The total number of links is %d.' %maxnum)
        print ('[OK] Mission complete: The number of links excluding duplication is %d.' %dnum)
        
        print ('[OK] The total running time is %s(min) %s(sec).' %(cm, cs))
        print ('[OK] Please check the result file. (./%s)' %outputFile)
else:
        print ('[ERR] Initialization faliure')