import json
import os
import boto3
import botocore
import random

from botocore.vendored import requests

# Get DynamoDB Client
client = boto3.client('dynamodb')

# Load environment variables
TELE_TOKEN = os.environ['TELE_TOKEN']
URL = f"https://api.telegram.org/bot{TELE_TOKEN}/"
COUNTRY_INFOS_TABLE = os.environ['COUNTRY_INFOS_TABLE']
PLAYER_INFOS_TABLE = os.environ['PLAYER_INFOS_TABLE']
REGISTRATION_COMMAND = os.environ['REGISTRATION_COMMAND']
QUIZ_COMMAND = os.environ['QUIZ_COMMAND']
NUMBER_OF_QUESTIONS = os.environ['NUMBER_OF_QUESTIONS']

# Load a DynamoDB Table
def load_dynamodb_table(table):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table)
    return table

# Send a Telegram Message to a given Chat ID
def send_message(text, chat_id):
    final_text = text
    url = URL + f"sendMessage?text={final_text}&chat_id={chat_id}"
    requests.get(url)

# Adds a new player to the Player Database
def register_player(telegram_message):
    response = client.put_item(
        TableName=PLAYER_INFOS_TABLE,
        Item={
            'id': {
                'N': str(telegram_message['chat']['id'])
            },
            'name': {
                'S': telegram_message['text']
            },
            'first_name': {
                'S': telegram_message['chat']['first_name']
            },
            'last_name': {
                'S': telegram_message['chat']['last_name']
            },
            'registration_status': {
                'S': "waiting_for_registration"
            },
            'game_mode': {
                'S': "main_menu"
            },
            'game_counter': {
                'N': "0"
            },
            'last_game_choice': {
                'N': "0"
            }
        }
    )

    return response

# Adds a new player to the Player Database
def update_player_info(telegram_message, registration_status=None, name=None, game_mode=None, game_counter=None, last_game_choice=None):

    Key = {
        'id': {
            'N': str(telegram_message['chat']['id'])
        }
    }

    switcher = {
        'registration_status': registration_status,
        'name': name,
        'game_mode': game_mode,
        'game_counter': game_counter,
        'last_game_choice': last_game_choice
    }

    updated_item = {}
    for attribute in switcher:
        if(switcher[attribute] != None):
            if(attribute != 'game_counter' and attribute != 'last_game_choice'):
                updated_item[attribute] = {'Value': {'S': switcher[attribute]}, 'Action': 'PUT'}
            else:
                updated_item[attribute] = {'Value': {'N': switcher[attribute]}, 'Action': 'PUT'}

    response = client.update_item(
        TableName=PLAYER_INFOS_TABLE,
        Key=Key,
        AttributeUpdates=updated_item
    )

    return response

# Gets the current registration_status for a player
def get_registration_status(telegram_message):
    response = client.get_item(
        TableName=PLAYER_INFOS_TABLE,
        Key={
            'id': {
                'N': str(telegram_message['chat']['id'])
            }
        }
    )

    if('Item' not in response):
        return 'Unregistered'
    else:
        return response['Item']['registration_status']['S']

# Helper Function to get country Information
def get_country_attribute(index_str, attribute, attribute_type):
    response = client.get_item(
        TableName=COUNTRY_INFOS_TABLE,
        Key={
            'index': {
                'N': index_str
            }
        }
    )

    return response['Item'][attribute][attribute_type]

# Get the current game counter
def get_game_counter(chat_id):
    response = client.get_item(
        TableName=PLAYER_INFOS_TABLE,
        Key={
            'id': {
                'N': str(chat_id)
            }
        }
    )

    return response['Item']['game_counter']['N']

# Get Information about the current player
def get_game_info(chat_id):
    response = client.get_item(
        TableName=PLAYER_INFOS_TABLE,
        Key={
            'id': {
                'N': str(chat_id)
            }
        }
    )

    return {
        'game_mode' : response['Item']['game_mode']['S'],
        'game_counter': response['Item']['game_counter']['N'],
        'last_game_choice': response['Item']['last_game_choice']['N']
    }

# Main Lambda Handler
def lambda_handler(event, context):

    # Registers the player if he/she is unknown
    telegram_event = event

    # Get most important Information from the event
    telegram_message = telegram_event['message']
    telegram_text = telegram_event['message']['text']
    chat_id = telegram_event['message']['chat']['id']

    # Get the Registration Status for this Person
    registration_status = get_registration_status(telegram_message)

    # Get the current Game registration_status
    if(registration_status == "Unregistered" and telegram_text != REGISTRATION_COMMAND):
        send_message("Please register first by sending the " + REGISTRATION_COMMAND + " command", chat_id)
        return {
            'registration_statusCode': 200
        }
    # Register the Person if he/she is new to the game
    elif(registration_status == 'Unregistered' and telegram_text == REGISTRATION_COMMAND):
        send_message("Welcome to the Game!\nPlease enter your player name", chat_id)
        register_player(telegram_message=telegram_message)
        return {
            'registration_statusCode': 200
        }

    # Update the Player Name
    if(registration_status == "waiting_for_registration"):
        update_player_info(telegram_message=telegram_message, registration_status="registered", name=telegram_text)
        send_message("Successfully updated your player name!", chat_id)
        return {
            'registration_statusCode': 200
        }

    # The person tries to register again
    if(registration_status == "registered" and telegram_text == REGISTRATION_COMMAND):
        send_message("You are already registered", chat_id)
        return {
            'registration_statusCode': 200
        }
    # Get the Game Counter if the Person is already registered
    if(registration_status == "registered" and telegram_text != REGISTRATION_COMMAND):
        game_counter = get_game_counter(chat_id)

    # Start the Quiz
    if(game_counter == "0" and telegram_text == QUIZ_COMMAND):

        # Select a random country
        number_of_countries = 242
        random_integer = str(random.randint(0, number_of_countries))
        random_country = get_country_attribute(index_str=random_integer, attribute='country', attribute_type='S')

        # Update the Player Information Table
        update_player_info(telegram_message=telegram_message, game_mode="quiz", game_counter=NUMBER_OF_QUESTIONS, last_game_choice=random_integer)

        send_message("What is the capital city of the following country?\n\n" + random_country, chat_id)

    if(int(game_counter) >= 0 and telegram_text != QUIZ_COMMAND):

        # Get Information about the running game
        game_info = get_game_info(chat_id)

        # Get the correct answer
        correct_answer = get_country_attribute(index_str=game_info['last_game_choice'], attribute='capital', attribute_type='S')

        # Inform the Player if he/she was right/wrong
        if(telegram_text == correct_answer):
            send_message("Your answer was correct!", chat_id)
        else:
            send_message("Sorry! The correct answer was " + correct_answer, chat_id)

        # Select another random country
        number_of_countries = 242
        random_integer = str(random.randint(0, 242))
        random_country = get_country_attribute(index_str=random_integer, attribute='country', attribute_type='S')

        # Update the Player Information Table
        if(int(game_counter) == 0):
            update_player_info(telegram_message=telegram_message, game_mode="main_menu")
            send_message("Thank you for playing!", chat_id)
        else:
            # Select a random country
            number_of_countries = 242
            random_integer = str(random.randint(0, number_of_countries))
            random_country = get_country_attribute(index_str=random_integer, attribute='country', attribute_type='S')
            update_player_info(telegram_message=telegram_message, game_counter=str(int(game_counter) - 1), last_game_choice=random_integer)
            send_message("What is the capital city of the following country?\n\n" + random_country, chat_id)



    return {
        'registration_statusCode': 200
    }
