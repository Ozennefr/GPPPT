# GPPPT
A simple one file python script to read a yaml file defining AI process. 

## The DSL

We designed a yaml based DSL to allow the definition of multistep processes and automate their execution by AI agents. 
Each process step is made of a prompt executed by a specified agent, and a validation substep executed by a second agent. The vaildation step is in charge of selecting the next step via a yes no answer.

Agents are defined in a specific section. For now, 4 agent types are defined:
- chat_agent: openai chatgpt agent
- vector search: agent that embed the prompt and find the closest on in a corpus
- mock agent: always answer with "response"
- input agent: prints the rpompt and returns user input

## Usage

make sure to put your openai apik in the env variable "OPENAI_KEY"

`python gpppt.py test.yml`

To use the whisky example, you need a feather file conataining whisky notes and their corresponding embeddings.
