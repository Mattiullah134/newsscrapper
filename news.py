from bs4 import BeautifulSoup
import datetime
import psycopg2
import requests
import json
from io import StringIO
import re

data_structure={
    'title':'',
    'description':'',
    'content':'',
    'date':'',
    'provider':'',
}
def api_call(url):
    try:
        # browser = webdriver.Chrome()
        # browser.get(url)
        # html = browser.page_source
        res = requests.get(url=url)
        soup = BeautifulSoup(res.content, 'html5lib') 
        return soup
    except Exception as e:
        print('Error while getting the data from {url}' , e)
        return None

def remove_special_chars(str):
    clean = re.sub(r'[^a-zA-Z ]', '', str)

    return clean

def db_connect():
    try: 
        conn = psycopg2.connect(dbname="postgres", user="postgres",password="password", host="localhost", port="5432" ) 
        conn.autocommit = True
        curr = conn.cursor()
        
        print("Database connected successfully")
        return curr
    except Exception as e:
        print("Database not connected successfully" , e)

def load_data_into_db(data):
    try:
        curr = db_connect()
        curr.execute("""
            create table if not exists news (
                id SERIAL PRIMARY KEY,
                url text,
                description text,
                title text,
                provider text,
                createdAt timestamp,       
                content text
            )
        """)
        insert_query = """
        INSERT INTO news (url ,description, title, provider, createdAt, content ) VALUES
        (%s,%s,%s,%s,%s,%s);
        """
        # Data to be inserted
        print(' data' , data)
        inserted_data = (
            data.get('url', '').strip(),  # Get 'url' or default to an empty string
            data.get('description', '').strip(),  # Get 'title' or default to an empty string
            data.get('title', '').strip(),  # Get 'price' or default to 0
            data.get('provider', '').strip(),  # Get 'uppercentage' or default to an empty string
            data.get('date', '').strip(),  # Get 'upprice' or default to an empty string
            data.get('content', '').strip() # Get 'timestamp' or default to an empty string
        )
        
        curr.execute(insert_query , inserted_data)
        print('data store ho gaya hai' , )
    except Exception as e:
        print("not able to store the data into db" , e)

def get_server_date():
    current_date = datetime.datetime.now()
    return current_date.strftime('%y-%m-%d %H:%M:%S')

def extract_data_from_bbc (url):
    soup = api_call(url=url) 
    bbc_news_data=[]
    main_content = soup.find('main' , attrs={'id':'main-content'})
    sections = main_content.find_all('section' )
    # print(sections)
    for sec in sections:
        data_divs = sec.find_all('div',attrs={'data-testid':'anchor-inner-wrapper'})
        for divs in data_divs:
            data_points = {}
            a=divs.find('a')
            if a:
                if a['href'].find('https') > -1:
                    data_points['url']=a['href']
                else:
                    data_points['url']=url.split('/news')[0] + a['href']
                h2=a.find('h2' , attrs={'data-testid':'card-headline'})
                p=a.find('p', attrs={'data-testid':'card-description'})
                if h2:
                    data_points['title']=remove_special_chars(h2.text)
                if p:
                    data_points['description']=p.text
                data_points['provider']='bbc'
                data_points['date']=get_server_date()
                # now find the content of the news
                print('url' , data_points['url'])
                if data_points['url'].find('articles') > -1:
                    content_soup = api_call(url=data_points['url'])
                    content_main = content_soup.find('main' , attrs={'id':'main-content'})
                    content_main_div = content_main.find_all('div' , attrs={'data-component':'text-block'})
                    if not content_main_div:
                        continue
                    for divdata in content_main_div:
                        content =  divdata.text.strip()
                        if 'content' in data_points.keys():
                            data_points['content'] =remove_special_chars(f"{data_points['content']} {content}".strip())
                        else:
                            data_points['content'] =remove_special_chars(content)

                elif data_points['url'].find('live') > -1:
                    content_soup = api_call(url=data_points['url'])
                    script = content_soup.find('script' , attrs={'data-testid':'live-blog-schema-data-script' , 'type':'application/ld+json'})
                    if not script:
                        continue
                    json_data = json.load(StringIO(script.string) )
                    pdata = json_data['@graph'][0]['liveBlogUpdate']
                    if pdata:
                        for p in pdata:
                            # print('p------------>', p.get('headline', ''), p.get('articleBody', ''))
                            content = f"{p.get('headline', '')} {p.get('articleBody', '')}".strip()
                            if 'content' in data_points:
                                data_points['content'] =remove_special_chars(f"{data_points['content']} {content}".strip())
                            else:
                                data_points['content'] = remove_special_chars(content)
    
                bbc_news_data.append(data_points)
                load_data_into_db(data=data_points)
                data_points={}
        
    print('bbc_news_data', bbc_news_data)

def extract_data_from_cnn (url):
    soup = api_call(url=url) 
    cnn_data=[]
    div_tag = soup.find_all('div' , attrs={'class':'zone__items layout--wide-center'} )
    for div_itr in div_tag:
        children = div_itr.find_all("div" , attrs={'class':'stack'})
        for child in children:
            div_children = div_itr.find_all("a" )
            for child in div_children:
                data_points = {}
                span = child.find('span' , attrs={'class':'container__headline-text'})
                if span:
                    data_points['title'] =remove_special_chars( span.text)
                    content_url = child['href']
                    if content_url.find('https') >= 0:
                        data_points['url'] = content_url
                    else:
                        data_points['url'] =url +  content_url
                    print('data_points[url]---------',data_points['url'])
                    if data_points['url'].find('video') == -1:
                        content_soup = api_call(url=data_points['url'])
                        
                        ptag = content_soup.find_all('p' , attrs={'class':'paragraph inline-placeholder vossi-paragraph'})
                        for p_itr in ptag:
                            if 'content' in data_points.keys():
                                data_points['content'] += remove_special_chars(f" {p_itr.text}")
                            else:
                                data_points['content'] = remove_special_chars(f"{p_itr.text}")
                        data_points['provider'] = 'cnn'
                        data_points['date'] = get_server_date()
                        load_data_into_db(data=data_points)
                        cnn_data.append(data_points)
                        data_points={}

    print('cnn_data---------------' , cnn_data)




    

def extract_data_from_dawn (url):
    soup = api_call(url=url) 
    dawn_data = []
    container = soup.find('div' , attrs={'class':'container px-0'})
    container.has_attr
    articles = container.find_all('article')
    for article_itr in articles:
        data_points={}
        a = article_itr.find('a' , attrs={'class':'story__link'})
        if not a:
            continue
        if a.has_attr('href'):
            news_url = a['href']
            data_points['title'] = remove_special_chars(a.text)
            data_points['url'] = news_url
            data_points['provider'] = 'dawn'
            data_points['date'] = get_server_date()
            print('news_url-------------' , news_url)
            content_soup = api_call(url=news_url)
            if news_url.find('live') >= 0:
                div = content_soup.find('div' , attrs={'class':'w-full sm:w-2/3 sm:px-6'})
                if div:
                    article = div.find_all('article')
                    for article_itr in article:
                        p_tag = article_itr.find_all('p')
                        for p_itr in p_tag:

                            if 'content' in data_points.keys():
                                data_points['content'] += remove_special_chars(f" {p_itr.text}")
                            else:
                                data_points['content'] = remove_special_chars(p_itr.text)
                else:
                    article = content_soup.find_all('article')
                    for article_itr in article:
                        p_tag = article_itr.find_all('p')
                        for p_itr in p_tag:

                            if 'content' in data_points.keys():
                                data_points['content'] += remove_special_chars(f" {p_itr.text}")
                            else:
                                data_points['content'] = remove_special_chars(p_itr.text)

            else:
                if news_url.find('youtube.com') >= 0:
                    continue
                if news_url.find('forms') >= 0:
                    continue
                article = content_soup.find('article' )
                if not article:
                    continue
                p_tag = article.find_all('p')
                for p_itr in p_tag:
                    if 'content' in data_points.keys():
                        data_points['content'] += remove_special_chars(f" {p_itr.text}")
                    else:
                        data_points['content'] = remove_special_chars(p_itr.text)

            dawn_data.append(data_points)
            print('data_point' , data_points)
            load_data_into_db(data_points)
            data_points={}
            
    
    print(dawn_data)




bbc_news='https://www.bbc.com/news'
cnn_news='https://edition.cnn.com'
dawn_news='https://www.dawn.com'

extract_data_from_bbc(url=bbc_news)
extract_data_from_cnn(url=cnn_news)
extract_data_from_dawn(url=dawn_news)