import yaml
import typer

app = typer.Typer()

def load_agents_from_plugin(plugin_list: list):
    agnts_constructors = {}
    for plugin in plugin_list:
        agnts_constructors.update(__import__(plugin).agents_constructors)

    return(agnts_constructors)

def parse_agents(agents_def, agents_constructors):
    agents = {
        key: agents_constructors[value['kind']](key, **value)
        for key, value in agents_def.items()
    }
    return agents

@app.command()
def parse(process_yaml):
    with open(process_yaml, 'r') as file:
        process = yaml.safe_load(file)
    
    agents_constructors = load_agents_from_plugin(process['agents_plugins'])
    agents = parse_agents(process["agents"], agents_constructors)
    max_process_length = process["process"]["max_process_length"]
    entrypoint = process["process"]["entrypoint"]
    variables = process.get("variables", {})

    print("Parsing successful!")

    return agents, entrypoint, process["steps"], variables, max_process_length

@app.command()
def draw(process_yaml:str, file_path:str):
    agents, entrypoint, steps, variables, max_process_length = parse(
        process_yaml
    )
    md = f"flowchart TD\n\tsubgraph Agents\n\t\tdirection LR"
    for agent, color in zip(agents, ['lightblue', 'lightgreen', 'orange', 'pink', 'lightgrey', 'white', 'yellow', 'red', 'green',]):
        md += f"\n\t\tclassDef {agent} fill:{color}"
        agent_type = str(type(agents[agent])).replace(
            "<class '", ""
        ).replace(
            "'>", ""
        )
        md += f"\n\t\t{agent}({agent} - {agent_type}):::{agent}"
    md += "\n\tend\n\n\tsubgraph Process"

    for step in steps:
        on_success = {entrypoint: 'end_of_process(( ))'}.get(
            steps[step]['on_success'], steps[step]['on_success']
        )
        on_failure = {entrypoint: 'end_of_process(( ))'}.get(
            steps[step]['on_failure'], steps[step]['on_failure']
        )
        md += f"\n\t\t{step}(step):::{steps[step]['agent']}"
        if on_success == on_failure:
            md += f"\n\t\t{step} --> {on_success}"
        else:
            md += f"\n\t\t{step} --> {step}_validation{{{{validation}}}}:::{steps[step]['validation']['agent']}"
            md += f"\n\t\t{step}_validation --Sucess--> {on_success}"
            md += f"\n\t\t{step}_validation --Failure--> {on_failure}"
    
    md += f"\n\t\tstart_of_process(( )) --> {entrypoint}"
    md += "\n\tend\n"
    md +="\n\t style Process fill:white,stroke:white"
    md +="\n\t style Agents fill:white,stroke:grey"

    with open(file_path, 'w') as file:
        file.write(md)


@app.command()
def run(process_yaml, verbose: bool=False):
    agents, entrypoint, steps, variables, max_process_length = parse(
        process_yaml
    )

    current_step = entrypoint
    context = {}

    n_step = 0
    while True:
        n_step += 1
        step = steps[current_step]
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
    app()
