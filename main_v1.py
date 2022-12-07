#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Builtins
import json
import os
import time
import re
# Local
from Classes import auth as Auth
from Classes import chat as Chat
from Classes import spinner as Spinner
from pathlib import Path
# Fancy stuff
import colorama
from colorama import Fore

colorama.init(autoreset=True)

# Check if config.json exists
if not os.path.exists("config.json"):
    print(">> config.json is missing. Please create it.")
    print(f"{Fore.RED}>> Exiting...")
    exit(1)

# Read config.json
with open("config.json", "r") as f:
    config = json.load(f)
    # Check if email & password are in config.json
    if "email" not in config or "password" not in config:
        print(">> config.json is missing email or password. Please add them.")
        print(f"{Fore.RED}>> Exiting...")
        exit(1)

    # Get email & password
    email = config["email"]
    password = config["password"]


def start_chat():
    expired_creds = Auth.expired_creds()
    print(f"{Fore.GREEN}>> Checking if credentials are expired...")
    if expired_creds:
        print(f"{Fore.RED}>> Your credentials are expired." + f" {Fore.GREEN}Attempting to refresh them...")
        # open_ai_auth = Auth.OpenAIAuth(email_address=email, password=password)
        open_ai_auth = Auth.OpenAIAuth(email_address=email, password=password)
        print(f"{Fore.GREEN}>> Credentials have been refreshed.")
        open_ai_auth.begin()
        time.sleep(3)
        is_still_expired = Auth.expired_creds()
        if is_still_expired:
            print(f"{Fore.RED}>> Failed to refresh credentials. Please try again.")
            exit(1)
        else:
            print(f"{Fore.GREEN}>> Successfully refreshed credentials.")
    else:
        print(f"{Fore.GREEN}>> Your credentials are valid.")

    print(f"{Fore.GREEN}>> Starting chat..." + Fore.RESET)
    previous_convo_id = None
    conversation_id = None
    access_token = Auth.get_access_token()


    prompt_filepaths = []
    base_dir = os.path.join("/Users/shailjathakur/Documents/date-llm-2023-main","prompts-and-testbenches/")
    # r=root, d=directories, f = files
    for r, d, f in os.walk(base_dir):
        for file in f:
            if (not file.startswith("tb") and not file.startswith("answer") and not file.startswith("example") and file.endswith(".v") ):
                prompt_filepaths.append(os.path.join(r, file))
    N=5

    for prompt_filepath in prompt_filepaths:
        pf = open(prompt_filepath, "r")
        file_lines = pf.readlines()
        prompt = ''.join(file_lines)


        tb="Generate test bench for the above code addressing the functionality and security of the code"
        prompts=[prompt, tb]
        # print(prompt)

        # get path of prompt directory
        p = Path(prompt_filepath)
        prompt_dir = p.parent

        for j,p in enumerate(prompts):
            for n in range(0,N):
                examples_dir_name = "examples"
                examples_dir = os.path.join(prompt_dir, examples_dir_name )
                
                if not os.path.isdir(examples_dir):
                    os.mkdir(examples_dir)
                    print("directory "+ examples_dir+" created")



                try:
                    filename = "example"+"_"+str(n)+"_"+str(j)+".v"

                    filecode = "example"+"_"+str(n)+"_"+str(0)+".v"


                    if os.path.exists(os.path.join(examples_dir,filename)): 
                        print(os.path.join(examples_dir,filename),'file exist')

                        # if os.path.exists(os.path.join(examples_dir,filecode)): 
                        if 'test bench' in p:
                            with open(os.path.join(examples_dir,filecode)) as f:
                                code=f.read()
                                p = code+tb
                                print('PROMPT') 
                                print(p)
                        continue

                    if access_token == "":
                        print(f"{Fore.RED}>> Access token is missing in /Classes/auth.json.")
                        exit(1)

                    # print('input prompt: ',p)
                    answer, previous_convo, convo_id = Chat.ask(auth_token=access_token,
                                                                prompt=p,
                                                                conversation_id=conversation_id,
                                                                previous_convo_id=previous_convo_id)
                    # print(answer)
                    # print(answer)
                    # create example file
                    if (not "Error" in answer): 

                        regex = re.compile(r"```(.+?)```", re.S)

                        match = regex.findall(answer)
                        
                        # print(match)
                        code=""
                        for m in match:
                            # print(m.group(1))
                            # print(m)
                            code+=m


                        if not bool(code):
                            print('RESPONSE IS EMPTY')
                            flag=False

                            while not flag:
                                print('Retrying ..')
                                answer, previous_convo, convo_id = Chat.ask(auth_token=access_token,
                                                                    prompt="Please complete the above code",
                                                                    conversation_id=conversation_id,
                                                                    previous_convo_id=previous_convo_id)
                                
                                if (not "Error" in answer): 


                                    regex = re.compile(r"```(.+?)```", re.S)

                                    match = regex.findall(answer)
                                    
                                    # print(match)
                                    code=""
                                    for m in match:
                                        code+=m

                                    if not (bool(code)): 
                                        continue
                                    else:
                                        print('RESPONSE: ',code)

                                        flag=True

                        else:
                            print('RESPONSE: ',code)


                    elif (("Error" in answer)):
                        flag=False
                        while not flag:
                            print('Retrying ..')
                            answer, previous_convo, convo_id = Chat.ask(auth_token=access_token,
                                                                prompt=p,
                                                                conversation_id=conversation_id,
                                                                previous_convo_id=previous_convo_id)
                            
                            if (not "Error" in answer) and (bool(answer)): 

                                regex = re.compile(r"```(.+?)```", re.S)

                                match = regex.findall(answer)
                                
                                # print(match)
                                code=""
                                for m in match:
                                    code+=m

                                if not (bool(code)):
                                    continue
                                else:
                                    print('RESPONSE: ',code)

                                    flag=True

                    

                    else:
                        print('UNKNOWN ERROR')

                    
                    
                    
                    with open( os.path.join(examples_dir,filename),'w' ) as fw:
                        fw.write(code)
                    fw.close()


                    if answer == "400" or answer == "401":
                        print(f"{Fore.RED}>> Your token is invalid. Attempting to refresh..")
                        open_ai_auth = Auth.OpenAIAuth(email_address=email, password=password)
                        # chat = Chat(email="email", password="password", proxies="http://localhost:8080")
                        open_ai_auth.begin()
                        time.sleep(3)
                        access_token = Auth.get_access_token()
                    else:
                        if previous_convo is not None:
                            previous_convo_id = previous_convo

                        if convo_id is not None:
                            conversation_id = convo_id

                        # print(answer)
                        # spinner.stop()
                        # print(f"Chat GPT: {answer}")
                except KeyboardInterrupt:
                    print(f"{Fore.RED}>> Exiting...")
                    exit(1)


if __name__ == "__main__":
    start_chat()
