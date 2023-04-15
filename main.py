# Imports
import requests
import re #regexp

# The following imports are used to tokenize and generate a summary of the content
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer as Summarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

# Obtain punkt (If error is generated)
#import nltk
#nltk.download('punkt')

def parse_data(data):
    """
    Parses and formats data obtained from Reddit submission
  
    Parameters:
    data (string): JSON of submission comments
  
    Returns:
    string: Content obtained from data input and formatted
  
    """
    parsedData = ""
    for i in range(0, len(data)-1):
        # Get content
        body = data[i]["body"]
        
        # Remove all newlines and whitespace
        body = re.sub('\s+', ' ', body)
        
        # Add data to parsedData
        parsedData = parsedData + body
    return parsedData

def base36_to_10(in_str: str) -> int:
    """
    Converts base36 numeral to base 10
  
    Parameters:
    in_str (string): Base36 id obtained from submission search 
  
    Returns:
    int: Base 10 integer
  
    """
    return int(in_str, 36)

def search_submission_comments(id, keyword):
    """
    Searches for all comments on a specific Reddit submission
  
    Parameters:
    id (string): Base36 id obtained from submission search 
  
    Returns:
    string: All comment content from the submission with the given id
  
    """
    subData = ""
    before_comment = ""
    previous_before = ""
    request_count = 0
    running = True

    while running:
        # Increment number of attempted requests
        request_count += 1

        # Attempt request to Pushshift API
        print("Attempting to load a comment request")

        response = ""
        url = "https://api.pushshift.io/reddit/comment/search?link_id="+str(id)+"&size=500&q="+keyword+"&before="+str(before_comment)
        try:
            response = requests.get(url)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)

        # Get JSON data
        data = response.json()["data"]
        length = len(data)

        # Check if response contains comments
        if (length == 0):
            break

        # Set before
        previous_before = before_comment
        before_comment = data[length-1]["updated_utc"]

        # Check if previous before is the same as the new before
        if (previous_before == before_comment):
            break

        # Get comment data and add it to txt
        subData = subData + parse_data(data)
    return subData

def submission_iteration(data, keyword):
    """
    Iterates through list of submissions, collecting data from all comments in each submission
  
    Parameters:
    data (string): JSON of submissons
  
    Returns:
    string: All comment content from the input list of submissions
  
    """
    postData = ""
    for post in data:
        # Get base36 id and convert it to base 10
        id = base36_to_10(post['id'])

        # Get comments (specifically content) from post
        postData = postData + search_submission_comments(id, keyword)
    return postData

def get_submissions(query, keyword, subreddits):
    """
    Gets a number of Reddit submissions using specific keywords and collects data from all comments
  
    Parameters:
    None
  
    Returns:
    string: All comment content from the submissions found
  
    """
    before_submission = ""
    txt = ""

    # Using to limit number of requests
    request_count = 0
    REQUEST_LIMIT = 1

    while request_count < REQUEST_LIMIT:
        # Increment number of attempted requests
        request_count += 1

        # Attempt request to Pushshift API
        print("Attempting to load submission request #"+str(request_count))

        response = ""
        url = "https://api.pushshift.io/reddit/search/submission?q="+query+"&subreddit="+subreddits+"&before="+str(before_submission)+"&size=500"
        try:
            response = requests.get(url)
        except requests.exceptions.RequestException as e:
            raise SystemExit(e)
        
        # Get JSON data
        data = response.json()["data"]
        length = len(data)

        # Check if response contains comments
        if (length == 0):
            break

        # Get comment data and add it to txt
        txt = txt + submission_iteration(data, keyword)

        # Set before
        before_submission = data[length-1]["updated_utc"]
    return txt

# BEGIN PROGRAM

# Prompt user for input
question = input("Please ask a question you want an answer to > ")
question.replace(" ", "+")

# Prompt user for keywords
keyword = input("Please enter ONE keyword relating to your request > ")

# Prompt user for subreddits
subreddits = input("Please enter related subreddits (separated by commas, no spaces) > ")

# Get submissions
txt = ""
txt = txt + get_submissions(question, keyword, subreddits)

print("INFO: All requests complete.")
print("Summarizing data...")

# You have your string of text, now summarize it
print("Now attempting to summarize. Please wait...")

LANGUAGE = "english"
SENTENCES_COUNT = 7

parser = PlaintextParser.from_string(txt, Tokenizer(LANGUAGE))
stemmer = Stemmer(LANGUAGE)

summarizer = Summarizer(stemmer)
summarizer.stop_words = get_stop_words(LANGUAGE)

# Print summary
for sentence in summarizer(parser.document, SENTENCES_COUNT):
    print(sentence)
