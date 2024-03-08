import os
import subprocess
import anthropic
import logging
import time
from tqdm import tqdm
from requests.exceptions import RequestException, ConnectionError, Timeout
import ast
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the Anthropic client with your API key
api_key = "APIKEY"
client = anthropic.Anthropic(api_key=api_key)

# Function to safely make a request with retries
def safe_request(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logging.error(f"Request failed with error: {e}")
        raise

# Function to execute the generated Python scripts
def execute_scripts(scripts):
    logging.info("Starting script execution...")
    for script in tqdm(scripts, desc="Executing scripts", unit="script"):
        try:
            with open("temp_script.py", "w") as file:
                file.write(script)
            subprocess.run(["python", "temp_script.py"], check=True)
            os.remove("temp_script.py")
        except Exception as e:
            logging.error(f"Error executing script: {e}")
    logging.info("Script execution completed.")

# Function to validate the generated scripts
def validate_scripts(scripts):
    for script in scripts:
        try:
            ast.parse(script)
        except SyntaxError as e:
            logging.error(f"Syntax error in generated script: {e}")
            return False
    return True

# Function to extract content from API response
def extract_content(response):
    if isinstance(response, list):
        return ' '.join([str(item) for item in response])
    elif isinstance(response, dict) or isinstance(response, anthropic.api.ContentBlock):
        # Assuming the response is a dict with a 'content' key or a ContentBlock object
        return response.get('content') if isinstance(response, dict) else response.content
    elif isinstance(response, str):
        return response
    else:
        raise ValueError("Unexpected response type")

# Function to generate MVP web application
def generate_mvp_web_app(prompt):
    start_time = time.time()
    model = "claude-3-opus-20240229"
   
    logging.info("Analyzing prompt...")
    analysis_prompt = f"This is a one-shot opportunity to analyze the following prompt and identify the key components and requirements for the web application. The instructions you provide will be used directly to create the project, so it's crucial to be comprehensive and accurate:\n{prompt}"
    analysis_response = safe_request(client.messages.create,
        model=model,
        max_tokens=200,
        messages=[{"role": "user", "content": analysis_prompt}]
    )
    analysis_content = extract_content(analysis_response.content)
    if "key components" not in analysis_content.lower() or "requirements" not in analysis_content.lower():
        raise ValueError("Prompt analysis response does not contain the necessary information.")
    logging.info(f"Prompt analysis completed. Response (first 100 tokens): {analysis_content[:100]}")
   
    logging.info("Determining tech stack...")
    tech_stack_prompt = f"This is a one-shot opportunity to determine the most suitable tech stack for the web application based on the following analysis. The chosen tech stack will be used directly to create the project, so ensure the recommendation is precise and well-justified:\n{analysis_content}"
    tech_stack_response = safe_request(client.messages.create,
        model=model,
        max_tokens=100,
        messages=[{"role": "user", "content": tech_stack_prompt}]
    )
    tech_stack_content = extract_content(tech_stack_response.content)
    logging.info("Outlining steps for MVP creation...")
    outline_prompt = f"This is a one-shot opportunity to outline the steps needed to create the MVP web application using the {tech_stack_content} tech stack. Include all necessary directories, files, and configurations. The instructions provided will be used directly to structure the project, so detail and accuracy are paramount:"
    outline_response = safe_request(client.messages.create,
        model=model,
        max_tokens=400,
        messages=[{"role": "user", "content": outline_prompt}]
    )
    outline_content = extract_content(outline_response.content)
    logging.info(f"MVP creation steps outlined. Response (first 100 tokens): {outline_content[:100]}")
   
    logging.info("Generating project structure scripts...")
    structure_prompt = f"This is a one-shot opportunity to generate Python scripts for creating the project structure, directories, and files based on the following detailed outline. The scripts generated will be executed to form the project's foundation, so ensure they are accurate and executable:\n{outline_content}"
    structure_response = safe_request(client.messages.create,
        model=model,
        max_tokens=1000,
        messages=[{"role": "user", "content": structure_prompt}]
    )
    structure_content = extract_content(structure_response.content)
    structure_scripts = structure_content.split("```python")[1:]
    structure_scripts = [script.split("```")[0].strip() for script in structure_scripts]
    if not validate_scripts(structure_scripts):
        raise ValueError("Generated structure scripts contain syntax errors.")
    logging.info(f"Project structure scripts generated. Number of scripts: {len(structure_scripts)}")
   
    logging.info("Generating code and configurations...")
    code_prompt = f"This is a one-shot opportunity to populate the created files with the appropriate code and configurations based on the {tech_stack_content} tech stack and the specific requirements of the web application. The code generated will be used directly in the project, so precision and completeness are crucial:\n{prompt}"
    code_response = safe_request(client.messages.create,
        model=model,
        max_tokens=2000,
        messages=[{"role": "user", "content": code_prompt}]
    )
    code_content = extract_content(code_response.content)
    code_scripts = code_content.split("```python")[1:]
    code_scripts = [script.split("```")[0].strip() for script in code_scripts]
    if not validate_scripts(code_scripts):
        raise ValueError("Generated code scripts contain syntax errors.")
    logging.info(f"Code and configurations generated. Number of scripts: {len(code_scripts)}")
   
    execute_scripts(structure_scripts)
    execute_scripts(code_scripts)
   
    logging.info("Validating generated project...")
    # Add project validation steps here
   
    logging.info("MVP web application generated successfully!")
    elapsed_time = time.time() - start_time
    logging.info(f"Total time taken: {elapsed_time:.2f} seconds")

# Get the single sentence prompt from the user
while True:
    prompt = input("Enter a >= 5 word sentence to generate the MVP web application: ")
    if len(prompt.split()) >= 5:
        break
    else:
        print("Prompt is too short. Please provide a more detailed sentence.")

# Generate the MVP web application
generate_mvp_web_app(prompt)