class Agent():
    def __init__(self, name, *, kind, roleplay=None, options=None):
        self.name = name
        self.kind = kind
        self.roleplay = roleplay or ""
        self.options = options or {}
        self.setup()

    def __call__(self, prompt, verbose=False):
        prompt = f'{self.roleplay} {prompt}'  
        answer = self.prompt(prompt)
        if verbose:
            print(f'Process: {prompt}')
            print(f'{self.name}: {answer}')
        return answer
    
    def setup(self):
        return None
    
    def prompt(self):
        raise NotImplementedError

class InputAgent(Agent):
    def prompt(self, prompt):       
        print(prompt)
        return input()

class MockAgent(Agent):
    def prompt(self, _):       
        return self.options.get('response', '')

agents_constructors = {
    'input': InputAgent, 
    'mock': MockAgent,
}