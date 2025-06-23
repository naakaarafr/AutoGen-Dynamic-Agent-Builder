import autogen
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
gemini_api_key = os.getenv('GEMINI_API_KEY')

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please check your .env file.")

# Configuration
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

class AutoAgentBuilder:
    """
    Custom AutoGen agent builder that uses LLM to automatically design agents
    """
    
    def __init__(self, llm_config):
        self.llm_config = llm_config
        
    def analyze_task_and_build_agents(self, task_description):
        """
        Use LLM to analyze task and automatically design appropriate agents
        """
        
        # Create a temporary agent to analyze the task
        task_analyzer = autogen.AssistantAgent(
            name="TaskAnalyzer",
            system_message="""You are an expert at analyzing tasks and designing multi-agent systems.
            
            When given a task, you must respond with ONLY a JSON object that defines the agents needed.
            
            The JSON format should be:
            {
                "agents": [
                    {
                        "name": "AgentName",
                        "role": "Brief role description",
                        "system_message": "Detailed system message for the agent",
                        "capabilities": ["capability1", "capability2"]
                    }
                ]
            }
            
            Design 3-5 specialized agents that can work together to complete the task.
            Make sure each agent has a distinct role and expertise.
            Include diverse capabilities like research, coding, analysis, writing, coordination.
            DO NOT include any text outside the JSON object.""",
            llm_config=self.llm_config
        )
        
        # Create a simple user proxy to get the response
        user_proxy = autogen.UserProxyAgent(
            name="TempUser",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            code_execution_config=False
        )
        
        print("🤖 Analyzing your task to design optimal agents...")
        
        # Get agent design from LLM
        analysis_prompt = f"""
        Analyze this task and design a team of specialized agents to complete it:
        
        TASK: {task_description}
        
        Design agents that can work together effectively. Consider what skills, knowledge, and capabilities are needed.
        Respond with ONLY the JSON object defining the agents.
        """
        
        # Start the conversation to get agent design
        user_proxy.initiate_chat(
            task_analyzer,
            message=analysis_prompt,
            max_turns=1
        )
        
        # Get the last message which should contain the JSON
        last_message = user_proxy.chat_messages[task_analyzer][-1]["content"]
        
        try:
            # Extract JSON from the response
            json_start = last_message.find('{')
            json_end = last_message.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = last_message[json_start:json_end]
                agent_specs = json.loads(json_str)
                return self._create_agents_from_specs(agent_specs, task_description)
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            print(f"⚠️  Error parsing agent specifications: {e}")
            print("📝 LLM Response:", last_message)
            return self._create_fallback_agents(task_description)
    
    def _create_agents_from_specs(self, agent_specs, task_description):
        """Create agents based on LLM specifications"""
        
        agents = []
        
        print(f"🏗️  Building {len(agent_specs['agents'])} custom agents...")
        
        for spec in agent_specs['agents']:
            # Enhance system message with task context
            enhanced_system_message = f"""
            TASK CONTEXT: {task_description}
            
            ROLE: {spec['role']}
            
            {spec['system_message']}
            
            Your capabilities include: {', '.join(spec.get('capabilities', []))}
            
            Work collaboratively with other agents to complete the overall task.
            Be proactive, thorough, and provide high-quality output.
            """
            
            # Determine if agent needs coding capabilities
            needs_coding = any(cap.lower() in ['coding', 'programming', 'development', 'scripting'] 
                             for cap in spec.get('capabilities', []))
            
            if needs_coding:
                # Create as UserProxyAgent for code execution
                agent = autogen.UserProxyAgent(
                    name=spec['name'],
                    human_input_mode="NEVER",
                    max_consecutive_auto_reply=10,
                    code_execution_config={
                        "work_dir": "agent_workspace",
                        "use_docker": False
                    },
                    system_message=enhanced_system_message
                )
            else:
                # Create as AssistantAgent
                agent = autogen.AssistantAgent(
                    name=spec['name'],
                    system_message=enhanced_system_message,
                    llm_config=self.llm_config
                )
            
            agents.append(agent)
            print(f"  ✓ Created {spec['name']} - {spec['role']}")
        
        # Always add a coordination agent
        coordinator = autogen.AssistantAgent(
            name="TaskCoordinator",
            system_message=f"""You are the task coordinator for: {task_description}
            
            Your responsibilities:
            - Coordinate the work of all agents
            - Ensure the task is completed efficiently
            - Synthesize results from different agents
            - Make final decisions and provide summaries
            - Keep the team focused on the main objective
            
            Guide the conversation and ensure quality output.""",
            llm_config=self.llm_config
        )
        agents.append(coordinator)
        print(f"  ✓ Created TaskCoordinator - Overall coordination")
        
        return agents
    
    def _create_fallback_agents(self, task_description):
        """Create basic agents if LLM analysis fails"""
        
        print("🔄 Using fallback agent creation...")
        
        agents = [
            autogen.AssistantAgent(
                name="PrimaryAgent",
                system_message=f"You are the primary agent responsible for: {task_description}. You should lead the effort and coordinate with other agents.",
                llm_config=self.llm_config
            ),
            autogen.AssistantAgent(
                name="SupportAgent",
                system_message=f"You are a support agent helping with: {task_description}. Provide assistance, analysis, and additional perspectives.",
                llm_config=self.llm_config
            ),
            autogen.UserProxyAgent(
                name="ExecutorAgent",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=5,
                code_execution_config={
                    "work_dir": "workspace",
                    "use_docker": False
                },
                system_message=f"You execute code and handle practical implementation for: {task_description}"
            )
        ]
        
        return agents

# Get task from user input
print("=" * 60)
print("🚀 AUTOGEN INTELLIGENT AGENT BUILDER")
print("=" * 60)
print("This system uses AI to automatically design and create specialized agents")
print("based on your specific task requirements.")
print("\nThe system will:")
print("• Analyze your task using AI")
print("• Design optimal agent roles and capabilities")
print("• Create specialized agents automatically")
print("• Coordinate multi-agent collaboration")
print("\nExamples of tasks:")
print("- Find and analyze academic papers from arxiv")
print("- Build a web application with user authentication")
print("- Analyze datasets and create data visualizations")  
print("- Scrape websites and generate content reports")
print("- Create a trading bot for cryptocurrency")
print("- Research and write a comprehensive report")
print("-" * 60)

building_task = input("\n📝 Please describe the task you want the agents to accomplish:\n> ").strip()

if not building_task:
    print("No task provided. Using default task...")
    building_task = "Find a paper on arxiv by programming, and analyze its application in some domain."

print(f"\n🎯 TASK: {building_task}")
print("\n" + "="*60)

try:
    # Initialize our custom agent builder
    builder = AutoAgentBuilder(llm_config)
    
    # Automatically design and create agents
    agent_list = builder.analyze_task_and_build_agents(building_task)
    
    print(f"\n✅ Successfully created {len(agent_list)} specialized agents!")
    print("\n🤖 Your AI-designed agent team:")
    for i, agent in enumerate(agent_list):
        print(f"  {i+1}. {agent.name}")
    
    # Create group chat with the automatically designed agents
    group_chat = autogen.GroupChat(
        agents=agent_list,
        messages=[],
        max_round=20,
        speaker_selection_method="auto"
    )
    
    manager = autogen.GroupChatManager(
        groupchat=group_chat,
        llm_config=llm_config
    )
    
    print(f"\n🎬 Starting multi-agent collaboration...")
    print("=" * 60)
    
    # Start the conversation
    agent_list[0].initiate_chat(
        manager,
        message=f"Team, let's work together to complete this task: {building_task}\n\nPlease coordinate your efforts and deliver high-quality results."
    )
    
except Exception as e:
    print(f"\n❌ Error during execution: {e}")
    print("\nTroubleshooting tips:")
    print("1. Check your API key is correct")
    print("2. Verify internet connectivity") 
    print("3. Ensure the Gemini API is accessible")
    print("4. Try with a simpler task description")