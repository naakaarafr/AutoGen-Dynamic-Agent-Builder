import autogen
from autogen.agentchat.contrib.agent_builder import AgentBuilder
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
gemini_api_key = os.getenv('GEMINI_API_KEY')

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please check your .env file.")

# 1. Configuration
config_list = [
    {
        'model': 'gemini-2.0-flash-exp',
        'api_key': gemini_api_key,
        'api_type': 'google'
    }
]

llm_config = {
    "config_list": config_list, 
    "seed": 42,
    "temperature": 0.7,
    "timeout": 60
}

# 2. Initialize AgentBuilder with proper configuration
builder = AgentBuilder(
    config_file_or_env=None,
    builder_model='gemini-2.0-flash-exp',
    agent_model='gemini-2.0-flash-exp'
)

# 3. Get task from user input
print("=" * 60)
print("AUTOGEN DYNAMIC AGENT BUILDER")
print("=" * 60)
print("This system will create specialized agents based on your task.")
print("The more detailed your task description, the better agents it will create.")
print("\nExamples of tasks:")
print("- Find and analyze academic papers from arxiv")
print("- Build a web application with user authentication")
print("- Analyze datasets and create data visualizations")
print("- Scrape websites and generate content reports")
print("- Create a trading bot for cryptocurrency")
print("-" * 60)

building_task = input("\nPlease describe the task you want the agents to accomplish:\n> ").strip()

if not building_task:
    print("No task provided. Using default task...")
    building_task = "Find a paper on arxiv by programming, and analyze its application in some domain."

print(f"\nBuilding agents based on your task...")
print(f"Task: {building_task}")

try:
    # Build agents dynamically based on the task
    agent_list, agent_configs = builder.build(
        building_task=building_task,
        default_llm_config=llm_config,
        coding=True,  # Enable coding capabilities
        library_path_or_json=None,  # Let it create fresh agents
        max_agents=4  # Limit number of agents
    )
    
    print(f"\nSuccessfully created {len(agent_list)} agents based on your task:")
    for i, agent in enumerate(agent_list):
        print(f"  {i+1}. {agent.name} - {agent.system_message[:100]}...")
    
    # 4. Create multi-agent group chat with the dynamically created agents
    group_chat = autogen.GroupChat(
        agents=agent_list, 
        messages=[], 
        max_round=15,
        speaker_selection_method="auto"
    )
    
    manager = autogen.GroupChatManager(
        groupchat=group_chat, 
        llm_config=llm_config
    )
    
    print("\nStarting multi-agent conversation...")
    
    # 5. Initiate the conversation with your specific request
    conversation_starter = """
    Find a recent paper about GPT-4 or transformer models on arxiv from 2024. 
    Use programming to search and retrieve the paper, then analyze its contributions 
    and potential applications in real-world domains.
    """
    
    # Start the conversation
    agent_list[0].initiate_chat(
        manager, 
        message=conversation_starter
    )
    
except Exception as e:
    print(f"Error during agent building: {e}")
    print("\nThis might be due to:")
    print("1. API key issues")
    print("2. Model availability")
    print("3. Network connectivity")
    print("4. AgentBuilder configuration")
    
    # You can modify the task and try again
    print(f"\nTrying with a simpler task configuration...")
    
    # Alternative approach with different parameters
    try:
        simple_task = "Create agents to search and analyze academic papers from online sources"
        
        agent_list, agent_configs = builder.build(
            building_task=simple_task,
            default_llm_config=llm_config,
            coding=False  # Disable coding if there are issues
        )
        
        print(f"Created {len(agent_list)} agents with simpler configuration")
        
        group_chat = autogen.GroupChat(
            agents=agent_list,
            messages=[],
            max_round=10
        )
        
        manager = autogen.GroupChatManager(
            groupchat=group_chat,
            llm_config=llm_config
        )
        
        agent_list[0].initiate_chat(
            manager,
            message="Find and analyze a recent AI research paper"
        )
        
    except Exception as e2:
        print(f"Second attempt also failed: {e2}")
        print("Please check your API key and model availability")

# Optional: Save the agent configurations for reuse
def save_agent_configs(agent_configs, filename="agent_configs.json"):
    """Save agent configurations to reuse later"""
    import json
    try:
        with open(filename, 'w') as f:
            json.dump(agent_configs, f, indent=2)
        print(f"Agent configurations saved to {filename}")
    except Exception as e:
        print(f"Could not save configurations: {e}")

# Uncomment the line below if you want to save the agent configs
# save_agent_configs(agent_configs)