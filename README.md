# GPPPT
A simple one file python script that executes AI processes defined in YML. 

GPPPT stands for "processes processes processes", also known as "la règle des trois P".

## The DSL

We designed a yaml based DSL to allow the definition of multistep processes and automate their execution by AI agents. 
Each process step is made of a prompt executed by a specified agent, and a validation substep executed by a second agent. The validation step is in charge of selecting the next step via a yes no answer.

### DSL Quickstart
- Define the process name and entrypoint: Start by defining the name of the process and its entrypoint. The entrypoint is the first step of the process and is the point at which the process begins.

- Define the maximum length of the process: You can specify the maximum length of the process, after which it will fail.

- Define the agents: Next, define the agents that will be involved in the process. In your case, you have four agents - manager, worker, bookeeper, and user. You can specify the roleplay, kind, and options for each agent.

- Define the variables: You can define any variables that will be used in the process. For example, you have defined a variable note_example which is used in the hallucinate step.

- Define the steps: Finally, define the steps that will be executed in the process. Each step has an agent, a prompt, and a validation substep. The validation substep is mandatory, but you can fake it with a mock agent to make sure it always pass (see the `fail` step in the example). Each step also has an on_success and an on_failure action that will be taken based on the answer given by the agent.

### Agents
Agents are defined in two specific sections. 
First, we need to define the plugin list `agents_plugins`, containing the python modules we can load to define agents. Then, the `agents` section define the agents and their options. For now, 4 agent types are defined:
- chat_agent: openai chatgpt agent (oai_agent)
- vector search: agent that embed the prompt and find the closest on in a corpus (oai_agent)
- mock agent: always answer with "response" (base_agent)
- input agent: prints the prompt and returns user input (base_agent)

## Usage

make sure to put your openai apik in the env variable "OPENAI_KEY"

````
Usage: main.py [OPTIONS] COMMAND [ARGS]...         
Commands:
  draw                          
  parse                           
  run                             
````
### Run
Execute the process
````
$ python3 gpppt/main.py run test.yml
Parsing successful!
 what can i do for you today ?
something to go with rice
 lorem ipsum.

Here is the complete note : lorem ipsum.. 


 Type any key to start the process over.
````

To use the whisky example, you need a feather file conataining whisky notes and their corresponding embeddings.


### Draw
Draw the process as mermaid code

````
$ python3 gpppt/main.py drawe whisky_reco.yml
````

````mermaid
flowchart TD
	subgraph Agents
		direction LR
		classDef manager fill:lightblue
		manager(manager - gpppt_oai_agents.ChatAgent):::manager
		classDef worker fill:lightgreen
		worker(worker - gpppt_oai_agents.ChatAgent):::worker
		classDef bookeeper fill:orange
		bookeeper(bookeeper - gpppt_oai_agents.VectorSearchAgent):::bookeeper
		classDef user fill:pink
		user(user - gpppt_base_agents.InputAgent):::user
		classDef no_val fill:lightgrey
		no_val(no_val - gpppt_base_agents.MockAgent):::no_val
		classDef mock_worker fill:white
		mock_worker(mock_worker - gpppt_base_agents.MockAgent):::mock_worker
		classDef mock_manager fill:yellow
		mock_manager(mock_manager - gpppt_base_agents.MockAgent):::mock_manager
	end

	subgraph Process
		ask(step):::user
		ask --> ask_validation{{validation}}:::manager
		ask_validation --Sucess--> reformulate
		ask_validation --Failure--> end_of_process(( ))
		reformulate(step):::worker
		reformulate --> reformulate_validation{{validation}}:::manager
		reformulate_validation --Sucess--> detail
		reformulate_validation --Failure--> reformulate
		detail(step):::worker
		detail --> detail_validation{{validation}}:::manager
		detail_validation --Sucess--> hallucinate
		detail_validation --Failure--> reformulate
		hallucinate(step):::worker
		hallucinate --> hallucinate_validation{{validation}}:::manager
		hallucinate_validation --Sucess--> lookup
		hallucinate_validation --Failure--> reformulate
		lookup(step):::bookeeper
		lookup --> lookup_validation{{validation}}:::manager
		lookup_validation --Sucess--> recommendation
		lookup_validation --Failure--> reformulate
		recommendation(step):::worker
		recommendation --> recommendation_validation{{validation}}:::manager
		recommendation_validation --Sucess--> stop
		recommendation_validation --Failure--> reformulate
		fail(step):::user
		fail --> end_of_process(( ))
		stop(step):::user
		stop --> end_of_process(( ))
		start_of_process(( )) --> ask
	end

	 style Process fill:white,stroke:white
	 style Agents fill:white,stroke:grey
````

## Changelog
- 12/03: first working version
- 26/03: 
  - refactor agents in "plugins"
  - refactor main in subcommands
  - add parse command to check if the DSL has issues
  - add draw command the generates mermaid code representing the process and agents.

## Backlog
- Publish on pipy
- Publish agents on pypi
- Polish whisky recommender and ship it
- Smarter backtracking: keep k options at each generation and explore the tree depth first
- Develop other usecases

## ChatGPT generated yml (One shot - not parsing but close)
### Tech support
````yml
process:
  name: TechSupport
  entrypoint: ask_issue
  max_process_length: 10
  on_max_process_length: fail

agents_plugins:
  - gpppt_base_agents
  - gpppt_oai_agents

agents:
  customer:
    kind: input
  agent:
    roleplay: "As a technical support agent helping customers with their technical issues"
    kind: chat
    options:
      model: gpt-3.5-turbo
      memory: 3
  mock_agent:
    kind: mock
    options:
      response: "I am not sure what the issue is."

variables:
  support_email: "support@company.com"

steps:
  ask_issue:
    agent: customer
    prompt: "Please describe the issue you are experiencing."
    validation:
      prompt: "Can you confirm that the issue you are experiencing is `{customer_answer}`? Answer with only Yes or No."
      agent: agent
    on_success: ask_troubleshooting_steps
    on_failure: ask_issue

  ask_troubleshooting_steps:
    agent: agent
    prompt: "Have you tried any troubleshooting steps? If so, please describe them."
    validation:
      prompt: "Can you confirm that you have tried the following troubleshooting steps: `{agent_answer}`? Answer with only Yes or No."
      agent: agent
    on_success: offer_solution
    on_failure: ask_troubleshooting_steps

  offer_solution:
    agent: agent
    prompt: "Based on the issue you described and the troubleshooting steps you have tried, I recommend trying the following solution: `{solution}`. Do you want me to email you the instructions for the solution?"
    validation:
      prompt: "Can you confirm that you want me to email you the instructions for the solution to `{customer_answer}`? Answer with only Yes or No."
      agent: agent
    on_success: send_email
    on_failure: offer_alternative

  offer_alternative:
    agent: agent
    prompt: "If the recommended solution does not work, would you like to try an alternative solution? If so, please describe the issue in more detail."
    validation:
      prompt: "Can you confirm that you would like to try an alternative solution for the issue `{customer_answer}`? Answer with only Yes or No."
      agent: agent
    on_success: ask_issue
    on_failure: ask_issue

  send_email:
    agent: agent
    prompt: "What is the email address you would like me to send the instructions to?"
    validation:
      prompt: "Can you confirm that the email address you want me to send the instructions to is `{customer_answer}`? Answer with only Yes or No."
      agent: agent
    on_success: end_process
    on_failure: send_email

  end_process:
    agent: agent
    prompt: "Thank you for contacting technical support. Please check your email for the solution instructions. Is there anything else I can help you with?"
    validation:
      prompt: "Can you confirm that the issue `{customer_answer}` has been resolved? Answer with only Yes or No."
      agent: mock_agent
    on_success: stop
    on_failure: ask_issue

  fail:
    agent: customer
    prompt: "Sorry, I cannot proceed with the given issue. Let's end the process here. \n\n\n Type any key to start the process over."
    validation:
      prompt: ""
      agent: no_val
    on_success: ask_issue
    on_failure: ask_issue

  stop:
    agent: customer
    prompt
````

