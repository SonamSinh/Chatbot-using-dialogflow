from flask import Flask, make_response
from flask import request
import requests
import logging
import json
from bs4 import BeautifulSoup as SOUP 
import re 
import requests as HTTP 
import pandas as pd
import imdb

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s')

app = Flask(__name__)

ia = imdb.IMDb()

# all requests from dialogflow will go throught webhook function
@app.route('/webhook', methods=['POST'])
def webhook():
    # get dialogflow request
    req = request.get_json(silent=True, force=True)
    logger.info("Incoming request: %s", req)
    intent = get_intent_from_req(req)
    logger.info('Detected intent %s', intent)     
                                   
    if intent == 'Movie-list':
        genre = req['queryResult']['parameters']['Genre']
        OTT = req['queryResult']['parameters']['OTT_channels']
		company = ia.search_company(str(OTT))
        coid = company[0].companyID
        url = "https://www.imdb.com/search/title/?title_type=tvSeries&genres=" + str(genre) + "&companies=co" + str(coid) +"&sort=user_rating,desc"
        a = movie_title(url)
        count = 0
        my_list = {}
        for i in a:
            tmp = str(i).split('>')   # Splitting each line of the IMDb data to scrape movies 
            if(len(tmp) == 3):
                my_list[count]= tmp[1][:-3]
            if(count > 45):
                break
            count += 1
        final = pd.DataFrame(my_list.items(), columns =['Id','Movie'])
        final_list = movie_list(final)
        if final.empty:response = {'fulfillmentText': "Sorry, we don't have any list for above entries."}
        else:response = {'fulfillmentText': "Below is the list of series (Sorted by IMDb Rating Descending)" + "\n" + str(final_list) }
    
    res = create_response(response)
    return res

def get_intent_from_req(req): # Get intent name from dialogflow request
    try: intent_name = req['queryResult']['intent']['displayName']
    except KeyError: return None
    return intent_name

def movie_list(df):
    result = "S.No." + "   " + "Name " + "\n"
    i = 0
    for ind in df.index:
         result = result + str(i) + "   " + str(df['Movie'][ind]) + "\n"
         i = i + 1
    return result
    
def movie_title(url): 
    response = HTTP.get(url)   	# HTTP request to get the data of the whole page
    data = response.text        	# Parsing the data using BeautifulSoup 
    soup = SOUP(data, "lxml")
    title = soup.find_all("a", attrs = {"href" : re.compile(r'\/title\/tt+\d*\/')}) 	# Extract movie titles from the data using regex 
    return title

def create_response(response): #Creates a JSON with provided response parameters 
    res = json.dumps(response, indent=4)
    logger.info(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

if __name__ == '__main__':
    app.run(debug=True)
