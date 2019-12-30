tbbot

How to deploy the Bot to AWS?

Create a virtual environment first:
  $virtualenv --python=/usr/bin/python3 v-env

Activate the virtual environment:
  $source v-env/bin/activate

Create a package folder inside the project and switch to that folder.

Install the dependencies:
  $pip3 install --target ./ python-telegram-bot --upgrade

Deactivate the virtual environment:
  $deactivate

Create an AWS deployment package:
  $zip -r9 ~/tbbot/tbbot_lambda.zip .

Copy the lambda function code in src/tbbot_lambda.py to a file called lambda_function.py in the project folder.
Add the actual Lambda Function to the AWS deployment package (in project folder):
  $zip -g tbbot_lambda.zip lambda_function.py

If you have already created an AWS ApiGateway Endpoint with a Lambda Function you can run:
  $aws lambda update-function-code --function-name <your_lambda_function_name> --zip-file fileb://tbbot_lambda.zip
