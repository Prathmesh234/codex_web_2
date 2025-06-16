## This is the set up structure for the anchor browser 

## User profiles and how we will work with it 

We will be using clerk authentication in order to create the user profiles
First the user will login via clerk and clerk will generate a user id 
The user id will be our primary key in order to analyze all the user conversations

Next if the user does not exist, a search index will be created with their id-azure-search-index or something 
If the user already exists then we can just move to the next step 

Next after the user queries etc, we will use the user_id to create anchor browser profile for the user. The name of the profile will also be somethong like user_id-anchor-profile or something 

Now the user can start asking queries and conduct deep research. 

And then we can end the session 

## Log out procedure 

The user can log out easily without any diffculty in this case, the next time the user signs in using clerk authentication we will just add -anchor-profile at the end to get their profile id. This is generally unsafe but for MVP it seems plausible. 

## Multi Session Orchestration 

Master Agent (Memory fetching etc) -> Task Agent (Will determine how many sessions to run and tasks per session) -> Anchor_Session_Agent (this will be a azure function call where the agent will call the function number of sessions it wants, the output will be a session id or something) -> For each session id we will then run our browser us agent 