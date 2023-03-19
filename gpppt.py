import yaml
import pandas as pd
import numpy as np
import openai
import typer
import os
from dataclasses import dataclass, field
from typing import Any

openai.api_key = os.environ.get('OPENAI_KEY')

@dataclass
class Agent():
    name: str
    kind: str
    roleplay: str = ''
    options: dict = field(default_factory=dict)

    def __call__(self, prompt, verbose=False):
        prompt = f'{self.roleplay} {prompt}'  
        answer = self.prompt(prompt)
        if verbose:
            print(f'Process: {prompt}')
            print(f'{self.name}: {answer}')
        return answer

class InputAgent(Agent):
    def prompt(self, prompt):       
        print(prompt)
        return input()

class MockAgent(Agent):
    def prompt(self, _):       
        return self.options.get('response', '')

class ChatAgent(Agent):
    messages: list
    memory: int
    model: str

    def __init__(self, *args, **kwargs):
        super(ChatAgent, self ).__init__(*args, **kwargs)

        self.memory = self.options.get('memory', 1)
        self.model = self.options['model']
        self.messages = []

    def prompt(self, prompt): 
        self.messages.append({"role": "user", "content": prompt})
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=self.messages[-self.memory:],
            max_tokens=1024, n=1, stop=None, temperature=0.5,
        )
        answer = response["choices"][0]["message"]
        self.messages.append(answer)
        return answer["content"]

class VectorSearchAgent(Agent):
    txt_col: list = field(default_factory=list)
    emb_col: int
    model: str
    db: Any
    
    def __init__(self, *args, **kwargs):
        super(VectorSearchAgent, self ).__init__(*args, **kwargs)

        self.emb_col = self.options['vector_col']
        self.txt_col = self.options['text_col']
        self.model = self.options['model']
        self.db = pd.read_feather(self.options['filename']).assign(
            **{self.emb_col: lambda df: df[self.emb_col].apply(np.array)}
        )

    def get_embedding(self, text):
        text = text.replace("\n", " ")
        return openai.Embedding.create(
            input = [text], model=self.model
        )['data'][0]['embedding']

    def prompt(self, prompt):
        chatbot_vector = self.get_embedding(prompt)
        similarities = [\
            np.dot(chatbot_vector, vec) 
            for vec in self.db[self.emb_col].to_list()
        ]
        most_similar_index = np.argmax(similarities)
        return self.db.iloc[[most_similar_index],:].to_dict('records')[0][self.txt_col]

agents_constructors = {
    'chat_agent': ChatAgent, 'vector_search': VectorSearchAgent, 'input': InputAgent, 'mock_agent': MockAgent
}

def parse_agents(agents_def):
    agents = {
        key: agents_constructors[value['kind']](key, **value)
        for key, value in agents_def.items()
    }
    return agents

def execute_process(process_yaml, verbose: bool=False):
    with open(process_yaml, 'r') as file:
        process = yaml.safe_load(file)
    
    agents = parse_agents(process["agents"])
    max_process_length = process["process"]["max_process_length"]
    entrypoint = process["process"]["entrypoint"]
    variables = process.get("variables", {})

    current_step = entrypoint
    context = {}

    n_step = 0
    while True:
        n_step += 1
        step = process["steps"][current_step]
        agent = agents[step['agent']]
        prompt = step["prompt"].format(**context, **variables)
        response = agent(prompt, verbose)
        context[f'{current_step}_answer'] = response
        
        validation = step['validation']
        agent = agents[validation['agent']]
        validation_prompt = validation["prompt"].format(**context, **variables)
        validation_response = agent(validation_prompt, verbose)

        if n_step >= max_process_length:
            current_step = "fail"
        elif validation_response.strip().lower()[:3] == "yes":
            current_step = step.get("on_success", "fail")
        else:
            current_step = step.get("on_failure", "fail")

if __name__ == "__main__":
    typer.run(execute_process)
