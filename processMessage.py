import json
import os
import requests
import re
from pymongo import MongoClient

# Reading environment variables and generating a Telegram Bot API URL
BOT_TOKEN = os.environ['BOT_TOKEN']
CHAT_ID = os.environ['CHAT_ID']
TELEGRAM_URL = "https://api.telegram.org/bot{}/sendMessage".format(BOT_TOKEN)
MONGODB_PASSWORD = os.environ['MONGODB_PASSWORD']
MONGODB_USER = os.environ['MONGODB_USER']

conn_str = ('mongodb+srv://'+MONGODB_USER+':'+MONGODB_PASSWORD+'@cluster0.2r2cif0.mongodb.net/?retryWrites=true&w=majority')
client = MongoClient(conn_str, connectTimeoutMS=30000, socketTimeoutMS=None, connect=False, maxPoolsize=1)
db = client['Kilimanjaro_VR']
coll = db['data']

# extract activity type from message
def get_activity(message_text):
    if '\U0001F3C3' in message_text:
        activity_type = 'run'
    elif '\U0001F6B4' in message_text:
        activity_type = 'bike'
    elif '\U0001F3CA' in message_text:
        activity_type = 'swim'
    elif '\U000026F7' in message_text:
        activity_type = 'biezki'
    else: activity_type = 'Error: activity type could not be determined'
    return activity_type

# extract distance from message - counting with , and .
def get_distance(message_text, compiled_regex):
    distance = compiled_regex.search(message_text).group()
    if distance:
        if ',' in distance:
            distance = float(distance.replace(',', '.'))
        else:
            distance = float(distance)
    else: distance = 'Error: distance could not be found'
    return distance

def recalc_distance(activity_type, distance):
    if activity_type == 'run':
        recalc_distance = distance
    elif activity_type == 'bike':
        recalc_distance = distance/5
    elif activity_type == 'swim':
        recalc_distance = distance
    elif activity_type == 'biezki':
        recalc_distance = distance/3
    else: recalc_distance = 'Error: couldnt recalculate distance'
    return recalc_distance

def lambda_handler(event, context):
    try:
        body=json.loads(event['body'])
        print(body)
        message_text = body['message']['text']

        key_activities = {'\U0001F3C3:', '\U0001F6B4:', '\U0001F3CA:', '\U000026F7:'}

        # pre compiling regex
        compiled_regex = re.compile(r'\d+(\.|\,)\d+|\d+')

        if any(activity in message_text for activity in key_activities):
            original_distance = get_distance(message_text)
            activity_type = get_activity(message_text)
            recalculated_distance = recalc_distance(activity_type, original_distance)

            # save data to mongodb
            coll.insert_one({
                        'athlete_first_name': body['message']['from']['first_name'],
                        'athlete_last_name': body['message']['from']['last_name'],
                        'original_distance': original_distance,
                        'recalculated_distance': recalculated_distance,
                        'activity_type': activity_type,
                        'date': body['message']['date']
                        })

            payload = {
                'chat_id': body['message']['chat']['id'],
                'text': 'zapisane',
                'reply_to_message_id': body['message']['message_id'],
                'disable_notification': 'True'
            }

            # send reply to telegram
            r = requests.post(TELEGRAM_URL, json=payload)

        return {
            'statusCode': 200
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 200
        }



