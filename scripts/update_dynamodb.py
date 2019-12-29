import boto3
import json

client = boto3.client('dynamodb')

DATA_FOLDER = '/home/tobias/country-json/src/'
TABLE_NAME = 'country_infos'

# Open Data Files
continent_json_file = open(DATA_FOLDER + "country-by-continent.json")
capital_json_file = open(DATA_FOLDER + "country-by-capital-city.json")
flag_json_file = open(DATA_FOLDER + "country-by-flag.json")

# Parse Data Files
continent_data = json.load(continent_json_file)
capital_data = json.load(capital_json_file)
flag_data = json.load(flag_json_file)

print(continent_data[0]['country'])

# Update DynamoDB Table
for index in range(0, len(continent_data)):
    print(index)
    response = client.put_item(
        TableName=TABLE_NAME,
        Item={
            'index': {
                'N': str(index)
            },
            'country': {
                'S': continent_data[index]['country']
            },
            'continent': {
                'S': continent_data[index]['continent']
            },
            'capital': {
                'S': capital_data[index]['city']
            },
            'flag_base64': {
                'S': flag_data[index]['flag_base64']
            }
        }
    )

# Close all Files
continent_json_file.close()
capital_json_file.close()
flag_json_file.close()
