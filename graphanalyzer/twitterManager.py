import sys
import tweepy
import time
import json
import secrets
from py2neo import Graph
from py2neo.ogm import Property, GraphObject, Related

consumer_keys = secrets.consumer_keys
consumer_secrets = secrets.consumer_secrets

access_tokens = secrets.access_tokens
access_token_secrets = secrets.access_token_secrets

current_user = 0

auth = tweepy.OAuthHandler(consumer_keys[current_user], consumer_secrets[current_user])
auth.set_access_token(access_tokens[current_user], access_token_secrets[current_user])
api = tweepy.API(auth)
print(api.me())
print('\n')

list = []
following = []
followed_by = []

try:
    graph = Graph(password=secrets.password)
    graph.begin()
    graph.delete_all()
except:
    print('Neo4J is not started, please initialize the DB and retry again')
    sys.exit()

is_not_last_tweet = True



def changeAccount():
    global api, current_user, hashtag
    try:
        auth = tweepy.OAuthHandler(consumer_keys[current_user], consumer_secrets[current_user])
        auth.set_access_token(access_tokens[current_user], access_token_secrets[current_user])
        api = tweepy.API(auth)
        print(api.me())
        print('\n')
    except:
        if current_user >= 4:
            current_user = 0
        else:
            current_user = current_user + 1
        changeAccount()

    # Step 2: Creating a Stream
    myStreamListener = MyStreamListener()
    myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener)

    # Step 3: Starting a Stream
    myStream.filter(track=[hashtag])


def checkRelationships(tweetObject):
    try:
        for x in list:
            friendship = api.show_friendship(source_id=tweetObject.id, target_id=x.id)
            if friendship[0].following == True:
                print("FOUND! FOLLOWING")
                tweetObject.Following.add(x)
            if friendship[1].followed_by == True:
                print("FOUND! FOLLOWED_BY")
                x.Following.add(tweetObject)
        graph.create(tweetObject)
    except tweepy.RateLimitError:
        print("Rate Limit Error")
        global current_user
        current_user = current_user + 1
        changeAccount()


# Using the streaming API has three steps.

# Step 1: Create a class inheriting from StreamListener
class MyStreamListener(tweepy.StreamListener):

    def __init__(self, time_limit=100):
        self.start_time = time.time()
        self.limit = time_limit
        super(MyStreamListener, self).__init__()

    def on_data(self, data):
        global is_not_last_tweet
        print("Is not last tweet :" + str(is_not_last_tweet))
        if is_not_last_tweet:
            if (time.time() - self.start_time) < self.limit:
                tweet = json.loads(data)
                tweetObject = Tweet()
                tweetObject.username = tweet['user']['screen_name']
                tweetObject.name = tweet['user']['name']
                tweetObject.time = tweet['created_at']
                tweetObject.location = tweet['user']['location']
                tweetObject.id = tweet['user']['id']
                tweetObject.profile_picture = tweet['user']['profile_image_url_https']
                try:
                    tweetObject.tweet = tweet['extended_tweet']['full_text']
                except KeyError:
                    tweetObject.tweet = tweet['text']
                list.append(tweetObject)
                checkRelationships(tweetObject)
                if (tweet['user']['verified'] == 'true'):
                    print('verified')
                else:
                    print('unverified')
                return True
            else:
                print(str(time.time() - self.start_time) + " " + str(self.limit))
                return False
        else:
            self.set_is_not_last_tweet(True)
        return True

    def on_error(self, status_code):
        print('Error raised: ' + str(status_code))
        if status_code == 420 & current_user == 0:
            connectToStream()
        elif status_code == 420 & current_user == 1:
            connectToStream()

    def set_is_not_last_tweet(self, status):
        global is_not_last_tweet
        is_not_last_tweet = status
        print("Is not last tweet status :" + str(is_not_last_tweet))

    def set_start_time(self):
        self.start_time = time.time()

class Tweet(GraphObject):
    __primarykey__ = "name"

    username = Property()
    name = Property()
    tweet = Property()
    time = Property()
    location = Property()
    id = Property()
    profile_picture = Property()
    Following = Related("Tweet", "FOLLOWING")
    Followed_by = Related("Tweet", "FOLLOWED_BY")

# Step 2: Creating a Stream
myStreamListener = MyStreamListener()
myStreamListener.set_is_not_last_tweet(True)


def connectToStream(word):
    print('Tracking: ' + word)
    global myStreamListener, hashtag, myStream
    myStreamListener.set_start_time()
    hashtag = word
    graph.begin()
    graph.delete_all()
    myStream = tweepy.Stream(auth=api.auth, listener=myStreamListener)

    # Step 3: Starting a Stream
    myStream.filter(track=[word])

def closeThread():
    global myStreamListener
    myStreamListener.set_is_not_last_tweet(False)
    myStream.disconnect()
    graph.delete_all()

    print('Disconnecting Thread looking for tweets related with: ' + hashtag)
