from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import requests.packages.urllib3
from urllib.parse import urljoin
from urllib.request import urlopen
from urllib.request import Request
import re
from lxml import html
import requests
from time import sleep
from random import randint

app = Flask(__name__)
session = requests.Session()
session.trust_env = False

#--------------------sentiment analysis------------------------------
def scrape_news_text(source):
    data = session.get(source).text
    news_soup = BeautifulSoup(data, 'html.parser')
    paragraphs = [par.text for par in news_soup.find_all('p')]
    paragraphs = paragraphs[2:-6]
    news_text = '\n'.join(paragraphs)
    #write_to_file(news_text)
    return news_text


def azure_sentiment(text):
    documents = {'documents': [
        {'id': '1', 'text': text}
    ]}
    azure_key = 'd38ac31a3b2c4e0982d3bc540251a162'
    azure_endpoint = 'https://canadacentral.api.cognitive.microsoft.com/text/analytics/v2.0'
    assert azure_key
    sentiment_azure = azure_endpoint + '/sentiment'
    headers = {"Ocp-Apim-Subscription-Key": azure_key}
    response = session.post(sentiment_azure, headers=headers, json=documents)
    sentiments = response.json()
    sentiments = sentiments['documents'][0]['score']
    return sentiments

def replace(text):
    list_of_words = text.split(" ")
    bad_list = ["bear", "bearish", "underperform", "underperforming", "sell", "selling", "sold", "decrease",
                "decreasing", "falling", "fall", "fell", "down", "lose", "lost", "losses", "losing", "downturn",
                "short", "shorting", "downside", "risky", "decline", "declining", "fear", "fears", "sell-off"]
    good_list = ["bull", "bullish", "overperform", "overperforming", "buy", "buying", "bought", "increase",
                 "increasing", "rising", "rise", "rised", "up", "gain", "gains", "gained", "profit", "profited","profitable", "profiting", "upturn", "upside"]
    list_of_words = ["bad" if word in bad_list else word for word in list_of_words]
    list_of_words = ["good" if word in good_list else word for word in list_of_words]
    list_of_words = " ".join(list_of_words)
    return list_of_words


def freq_chart(list_of_words):
    list_of_words = map(lambda x: x.lower(), list_of_words)
    list_of_words = sorted(list_of_words)
    list_of_words = remove_common_words(list_of_words)
    global sentance
    sentance = ' '.join(list_of_words)


def remove_common_words(listOfWords):
    commonWords = ["a", "about", "all", "also", "it", "the", "to", "of", "and", "in", "is", "for", "with", "that",
                   "has", "its", "as", "on", "this", "at", "will", "are", ".", "be", "an", "by", ",", "'", "from",
                   "have", "or", "than", "stock", "stocks", "said", "he", "not", "can", "i", "they", "when", "some",
                   "their", "we", "it's", "more", "was", "but", "one", "just", "so", "which", "these", "if", "they're",
                   "their", "could", "think", "that's", "there", "you", "get", "market", "very", "been", "year",
                   "other", "his", "right", "even", "any", "**", "percent", "company", "after", "shares", "next",
                   "investor's", "investors", "last", "trade", "price", "business", "zacks", "company's", "here", "inc",
                   "per", "click", "new", "--", "our", "fool", "each", "", "nasdaq", "(", ")", "were", "current",
                   "those", "-", "believe", "financial", "share", "percent.", "*", "", "motley", "over", "nasdaq:",
                   "percent,", "index", "would", "total", "them", "much", "my", "still", "into", "had", "since", "500", "s&p", "friday", "shares", "nasdaq", "trading", "day", "time", "to", 'like']
    cleanList = []
    for word in listOfWords:
        if word not in commonWords:
            cleanList.append(word)
    return cleanList


def get_articles(ticker):
    articles = []
    source = "https://www.nasdaq.com/symbol/" + ticker + "/news-headlines"
    for i in range(1):
        if i == 0:
            news = source
        else:
            news = source + "?page=" + str(i)
        url = requests.get(news)
        data = url.text

        soup = BeautifulSoup(data, 'html.parser')
        for link in soup.find_all('a'):
            current_link = link.get('href')
            if 'article' == current_link[23:30] and current_link not in articles:
                publish_date = str(link.parent.parent.find('small'))[31:41]
                publish_date = publish_date.strip(" ").split("/")
                if publish_date != ['']:
                    date_num = int(publish_date[2]) * 10000 + int(publish_date[0]) * 100 + int(publish_date[1])
                    articles.append([date_num, current_link])
    print(str(len(articles)) + " articles found")
    return articles

def write_to_file(text):
    file = open("news-articles.txt", "w")
    file.write(text)
    file.close()

def ave_sentiment(ticker):
    articles = get_articles(ticker)
    full_text = ""
    sentiment = 0
    for i in range(len(articles)):
        full_text = full_text + replace(scrape_news_text(articles[i][1]))
        print("Downloaded [" + str(i + 1) + "/" + str(len(articles)) + "]")

    #store all the news articles used for analysis
    write_to_file(full_text)

    #used to display frequent words on webpage
    freq_chart(full_text.split())

    #divide the entire text in sizes of 5000 chunks each and get the sentiment score
    breaks = int(len(full_text) / 5000)
    for i in range(breaks - 1):
        a = i * 5000
        b = (i + 1) * 5000
        sentiment = sentiment + azure_sentiment(full_text[a:b])
        print("sentiment score: ",sentiment / (i + 1))
    sentiment = sentiment + azure_sentiment(full_text[breaks * 5000:])
    sentiment = sentiment / breaks
    sentiment = sentiment * 100
    sentiment = int(round(sentiment))
    return sentiment

#----------------------------stock information---------------------------------------------
scraped_data = dict()

def parse_finance_page(ticker):
    """    input:
      ticker (str): Stock symbol

    output:
      dict: Scraped data
    """
    key_stock_dict = {}
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-GB,en;q=0.9,en-US;q=0.8,ml;q=0.7",
        "Connection": "keep-alive",
        "Host": "www.nasdaq.com",
        "Referer": "http://www.nasdaq.com",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36"
    }

    # disable / bypass proxy
    session = requests.Session()
    session.trust_env = False

    # Retrying for failed request
    for retries in range(5):
        try:
            url = "http://www.nasdaq.com/symbol/%s" % (ticker)
            response = session.get(url, headers=headers, verify=False)

            if response.status_code != 200:
                raise ValueError("Invalid Response Received From Webserver")

            print("Parsing %s" % (url))

            tree = html.fromstring(response.content)
            # Adding random delay
            sleep(randint(1, 3))
            parser = html.fromstring(response.text)
            xpath_head = "//div[@id='qwidget_pageheader']//h1//text()"
            xpath_last_price = "//*[@id='qwidget_lastsale']/text()"
            xpath_key_stock_table = '//div[@class="row overview-results relativeP"]//div[contains(@class,"table-table")]/div'
            xpath_key = './/div[@class="table-cell"]/b/text()'
            xpath_value = './/div[@class="table-cell"]/text()'


            raw_name = parser.xpath(xpath_head)
            key_stock_table = parser.xpath(xpath_key_stock_table)

            #still this works
            s = tree.xpath(xpath_last_price)

            raw_last_price = parser.xpath(xpath_last_price)

            company_name = raw_name[0].replace("Common Stock Quote & Summary Data", "").strip() if raw_name else ''
            last_price = raw_last_price[0].strip() if raw_last_price else None

            # Grabbing ans cleaning keystock data
            for i in key_stock_table:
                key = i.xpath(xpath_key)
                value = i.xpath(xpath_value)
                key = ''.join(key).strip()
                value = ' '.join(''.join(value).split())
                key_stock_dict[key] = value

            print(key_stock_dict)
            if('Market Cap' in key_stock_dict):
                    market_cap = key_stock_dict['Market Cap']
            if ("Today's High / Low" in key_stock_dict):
                todayshighlow = key_stock_dict["Today's High / Low"]

            if ('Previous Close' in key_stock_dict):
                previous_close = key_stock_dict['Previous Close']

            nasdaq_data = {

                "company_name": company_name,
                "Previous Close": previous_close,
                "Todays High/low":todayshighlow,
                "52 Week High / Low": key_stock_dict['52 Week High / Low'],
                "1 Year Target":key_stock_dict['1 Year Target'],
                "market cap": market_cap,
                "P/E Ratio":key_stock_dict['P/E Ratio']

            }
            return nasdaq_data,last_price

        except Exception as e:
            print("Failed to process the request, Exception:%s" % (e))


#---------------------------------transcript information----------------------------------------
def get_title(bsObj):
    title = bsObj.h1.text
    return title

def insert_backslash_comments(dirty_text):
    # code should backslash all quotes in our insert text
    backslash_single_quotes = dirty_text.replace("'", "\\'")
    backslash_double_quotes = backslash_single_quotes.replace("\"", "\\\"")
    return backslash_double_quotes

def get_ecall_text(bsObj, type):
    search = bsObj.findAll('div', {'itemprop': 'articleBody'})
    body = search[0]
    if type == 'dirty':
        return body
    else:
        dirty_text = body.text
        clean_text = insert_backslash_comments(dirty_text)
        return clean_text

def findTranscriptsURLs(ticker, n):
    url = urljoin('http://seekingalpha.com/symbol/', '/'.join([ticker, "earnings", "transcripts"]))
    r = requests.get(url, headers={'User-Agent':'Mozilla/5.0 (iPhone; CPU iPhone OS 5_0 like Mac OS X) AppleWebKit/534.46'})
    soup = BeautifulSoup(r.content, 'lxml')
    transcripts = []
    for link in soup.find_all("a"):
        x = link.get('href')
        if "earnings" in x and "transcript" in x:
            transcripts.append(urljoin('http://seekingalpha.com/', link.get("href")))
    return transcripts

#--------------------------------main----------------------------------------------------

@app.route('/')
def student():
    return render_template("input.html")

@app.route('/transcript',  methods=['POST', 'GET'])
def transcript():
    if request.method == 'POST':
        stock = request.form
        ticker = stock.get('Name')
        links = findTranscriptsURLs(ticker, 4)

        print("links :", links)
        #parsing only the first linked that is fetched
        url = links[0] + "?part=single"

        print("selected link----", url)
        content = Request(url, headers={
            'authority': 'seekingalpha.com',
            'method': 'GET',
            'path': '/earnings/earnings-call-transcripts',
            'scheme': 'https',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
        })

        html = urlopen(content)
        bsObj = BeautifulSoup(html.read(), 'lxml')
        title = get_title(bsObj)
        clean_text = get_ecall_text(bsObj, 'clean')
        output = clean_text.split('Operator')[0]
        text = output.split('\n')
        head = text[0]
        text.pop(0)
        return render_template("transcript.html", transcript = text, head = head, url =url, title = title)


@app.route('/stock',  methods=['POST', 'GET'])
def stock():
    if request.method == 'POST':
        stock = request.form
        ticker = stock.get('Name')
        dict,lastprice = parse_finance_page(ticker)
        return render_template("stock.html", res = dict, tick = ticker, lastprice = lastprice)

@app.route('/result', methods=['POST', 'GET'])
def result():
    if request.method == 'POST':
        result = request.form
        ticker = result.get('Name')
        analysis = str(ave_sentiment(result.get('Name')))
        print("Average sentiment score: ",analysis)
        links = get_articles(ticker)
        articles = str(len(links))
        links = links[:3]
        links = [links[0][1], links[1][1], links[2][1]]
        otherHalf = 100 - int(analysis)
        return render_template("output.html", art=articles, analysis=analysis, ticker=ticker, links=links, sentance=sentance, otherHalf=otherHalf)


if __name__ == '__main__':
    requests.packages.urllib3.disable_warnings()
    app.run(debug=True)