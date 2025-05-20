## The agent architecture for this would be the following 

## Orchestrator Agent (Main Agent) -> will decide how many instances to activate of the small agents and carefully analyze the task and distribute it between the multi agents. Access to browser agent and code agent 

## Can initialize as many code agents and browser agents it wants 

## Second layer - > Agents 

## Browser Agent, will be run via azure function and communicate with the orchestrator agent every time 
## Code Agent (responsible for writing and executing code ) -> will be run via azure function and communicate with the orchestrator agent too. 