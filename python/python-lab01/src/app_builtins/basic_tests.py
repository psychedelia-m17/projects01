import os
import re
import json


def do_pattern_check():
    response_string = 'HTTP 400: {\n\t\t\t\t\t\t\t\t\t        \t"message":"The account name Savings1 is already registered. Please select another name to continue creating the account."\n\t\t\t\t\t\t\t\t\t        }'
    response_string2 = 'HTTP 400: {"message":"The account name Savings1 is already registered. Please select another name to continue creating the account."}'
    response_string_slim = response_string2.replace("\n", "").replace("\t", "")
    print("Checking:\n", 50 * '-')
    print(response_string)
    print(response_string2)
    print(response_string_slim)
    print(50 * '-')

    pattern = r"^\s*HTTP (\d{3}):\s*(.*)"
    match = re.match(pattern, response_string_slim)

    if match:
        http_code = match.group(1)
        print("http_code:", http_code)
        # Extract the captured JSON string
        json_content = match.group(2)
        print(f"json_content: {json_content}")
        try:
            # Parse the string into a Python dictionary
            data = json.loads(json_content)
            print("Match found! Extracted JSON:", "\n",
                  data, "\n",
                  f"message: {data.get('message', 'No Message')}")
        except json.JSONDecodeError:
            print("Match found, but the extracted content is not valid JSON.")
    else:
        print("The string does not match the expected pattern.")

### --- Main section --------------
if __name__ == "__main__":
    current_directory = os.getcwd()
    print("Current Working Directory:", current_directory)

    do_pattern_check()
