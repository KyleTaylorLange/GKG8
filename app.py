#!/usr/bin/env python3

import os
import sys
import tweepy
import urllib.request
import json
from datetime import datetime
from influxdb import InfluxDBClient

<<<<<<< Updated upstream
# Quick variable to disable certain features for local testing purposes.
bIsLocalTest = False

=======
##Parse the environment vars from Config+Secret to the code.
>>>>>>> Stashed changes
def parseConfig():
    """Parse the environemnt variables and return them as a dictionary."""
    twitter_auth = ['TWITTER_API_KEY',
                    'TWITTER_API_SECRET',
                    'TWITTER_ACCESS_TOKEN',
                    'TWITTER_ACCESS_SECRET']

    twitter_user = ['TWITTER_USER']

    influx_auth = ['INFLUXDB_HOST',
                   'INFLUXDB_DATABASE',
                   'INFLUXDB_USERNAME',
                   'INFLUXDB_PASSWORD']

    weather_data = ['WEATHER_API_KEY',
                    'WEATHER_LOCATION']

    data = {}

    for i in twitter_auth, twitter_user, influx_auth, weather_data:
        for k in i:
            if k not in os.environ:
                raise Exception('{} not found in environment'.format(k))
            else:
                data[k] = os.environ[k]

    return(data)


def twitterApi(api_key, api_secret, access_token, access_secret):
    """Authenticate and create a Twitter session."""

    auth = tweepy.OAuthHandler(api_key, api_secret)
    auth.set_access_token(access_token, access_secret)

    return tweepy.API(auth)


def getUser(twitter_api, user):
    """Query the Twitter API for the user's stats."""
    return twitter_api.get_user(user)


def createInfluxDB(client, db_name):
    """Create the database if it doesn't exist."""
    dbs = client.get_list_database()
    if not any(db['name'] == db_name for db in dbs):
        client.create_database(db_name)
    client.switch_database(db_name)


def initDBClient(host, db, user, password):
    """Create an InfluxDB client connection."""

    client = InfluxDBClient(host, 8086, user, password, db)

    return(client)


def createPoint(username, measurement, value, time):
    """Create a datapoint."""
    json_body = {
        "measurement": measurement,
        "tags": {
            "user": username
        },
        "time": time,
        "fields": {
            "value": value
        }
    }

    return json_body

def getTemperatureIn(location_str, api_key):
    units_str = "&units=metric"
    API_str = "&appid=" + api_key
    url = "https://api.openweathermap.org/data/2.5/weather?q=" + location_str + units_str + API_str
    request = urllib.request.Request(url)
    r = urllib.request.urlopen(request).read()
    contents = json.loads(r.decode('utf-8'))
    return contents['main']['temp']

def main():
    """Do the main."""
    data = parseConfig()
    time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    twitter = twitterApi(data['TWITTER_API_KEY'],
                         data['TWITTER_API_SECRET'],
                         data['TWITTER_ACCESS_TOKEN'],
                         data['TWITTER_ACCESS_SECRET'])

    userdata = getUser(twitter, data['TWITTER_USER'])

    client = initDBClient(data['INFLUXDB_HOST'],
                          data['INFLUXDB_DATABASE'],
                          data['INFLUXDB_USERNAME'],
                          data['INFLUXDB_PASSWORD'])

    createInfluxDB(client, data['INFLUXDB_DATABASE'])
    

    json_body = []

    data_points = {
        "followers_count": userdata.followers_count,
        "friends_count": userdata.friends_count,
        "listed_count": userdata.listed_count,
        "favourites_count": userdata.favourites_count,
        "statuses_count": userdata.statuses_count
    }

    for key, value in data_points.items():
        json_body.append(createPoint(data['TWITTER_USER'],
                                     key,
                                     value,
                                     time))


    client.write_points(json_body)

    # Do weather separately.
    temp = -9
    json_body = []
    json_body.append(createPoint(data['TWITTER_USER'],
                                 "current_temperature",
                                 temp,
                                 time))

    client.write_points(json_body)


if __name__ == "__main__":
    sys.exit(main())
