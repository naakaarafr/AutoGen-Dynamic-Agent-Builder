import autogen
import os
import json
import time
import logging
import asyncio
import threading
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import random
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
gemini_api_key = os.getenv('GEMINI_API_KEY')

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please check your .env file.")

class TaskComplexity(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"

class RateLimitManager:
    """
    Advanced rate limiting manager with dynamic adjustment
    """
    
    def __init__(self, base_rpm: int = 8, is_paid_tier: bool = False):
        self.base_rpm = base_rpm
        self.is_paid_tier = is_paid_tier
        self.current_rpm = base_rpm
        self.request_times = []
        self.error_count = 0
        self.success_count = 0
        self.last_rate_limit_time = None
        
        # Dynamic adjustment parameters
        self.max_rpm = 60 if is_paid_tier else 15
        self.min_rpm = 3
        
    def get_current_limit(self) -> int:
        """Get current rate limit based on recent performance"""
        return self.current_rpm
        
    def can_make_request(self) -> bool:
        """Check if we can make a request now"""
        current_time = time.time()
        
        # Clean old requests
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        return len(self.request_times) < self.current_rpm
        
    def wait_if_needed(self) -> float:
        """Wait if needed, return wait time"""
        if self.can_make_request():
            self.request_times.append(time.time())
            return 0
            
        # Calculate wait time
        if self.request_times:
            oldest_request = min(self.request_times)
            wait_time = 60 - (time.time() - oldest_request) + random.uniform(1, 3)
        else:
            wait_time = 60 / self.current_rpm
            
        logger.info(f"⏳ Rate limit reached. Waiting {wait_time:.1f} seconds... (Current limit: {self.current_rpm} RPM)")
        time.sleep(wait_time)
        self.request_times.append(time.time())
        return wait_time
        
    def record_success(self):
        """Record successful request"""
        self.success_count += 1
        self.error_count = max(0, self.error_count - 1)  # Reduce error count on success
        
        # Gradually increase rate limit on success
        if self.success_count % 10 == 0 and self.current_rpm < self.max_rpm:
            self.current_rpm = min(self.current_rpm + 1, self.max_rpm)
            logger.info(f"📈 Increased rate limit to {self.current_rpm} RPM")
            
    def record_error(self, error_msg: str):
        """Record failed request and adjust rate limit"""
        self.error_count += 1
        self.last_rate_limit_time = time.time()
        
        # Decrease rate limit on repeated errors
        if self.error_count >= 3:
            self.current_rpm = max(self.current_rpm - 2, self.min_rpm)
            logger.warning(f"📉 Decreased rate limit to {self.current_rpm} RPM due to errors")
            self.error_count = 0  # Reset counter

class ResilientLLMConfig:
    """
    Advanced LLM configuration with resilient error handling
    """
    
    def __init__(self, base_config: Dict[str, Any], rate_manager: RateLimitManager):
        self.base_config = base_config
        self.rate_manager = rate_manager
        
    def get_config(self) -> Dict[str, Any]:
        """Get configuration with current settings"""
        config = self.base_config.copy()
        # Remove invalid parameters and only include valid AutoGen LLM config parameters
        config.update({
            "timeout": 180,
            # Removed max_retries as it's not a valid parameter for AutoGen LLM config
            # We handle retries manually in execute_with_retry method
        })
        return config
        
    def execute_with_retry(self, func, *args, **kwargs):
        """Execute function with intelligent retry logic"""
        max_retries = 5
        base_delay = 30
        
        for attempt in range(max_retries):
            try:
                self.rate_manager.wait_if_needed()
                result = func(*args, **kwargs)
                self.rate_manager.record_success()
                return result
                
            except Exception as e:
                error_str = str(e)
                
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    self.rate_manager.record_error(error_str)
                    
                    if attempt < max_retries - 1:
                        # Extract retry delay from error
                        retry_delay = self._extract_retry_delay(error_str, base_delay * (2 ** attempt))
                        logger.warning(f"🚫 Rate limit hit (attempt {attempt + 1}/{max_retries}). Waiting {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error("❌ Max retries exceeded for rate limiting")
                        raise Exception("Rate limit exceeded after maximum retries")
                        
                elif "QUOTA_EXCEEDED" in error_str:
                    logger.error("💳 API quota exceeded. Please check your billing.")
                    raise Exception("API quota exceeded")
                    
                else:
                    # Non-rate-limit errors
                    if attempt < 2:  # Retry once for other errors
                        logger.warning(f"⚠️ Error occurred: {error_str}. Retrying...")
                        time.sleep(5)
                        continue
                    else:
                        raise
                        
        return None
        
    def _extract_retry_delay(self, error_str: str, default_delay: int) -> int:
        """Extract retry delay from error message"""
        try:
            # Look for retryDelay in error message
            delay_match = re.search(r"'retryDelay': '(\d+)s'", error_str)
            if delay_match:
                return int(delay_match.group(1)) + random.randint(5, 10)
        except:
            pass
        return default_delay

class TaskComplexityAnalyzer:
    """
    Analyzes task complexity to determine optimal agent configuration
    """
    
    @staticmethod
    def analyze_complexity(task_description: str) -> TaskComplexity:
        """Analyze task complexity based on description"""
        task_lower = task_description.lower()
        
        # Enterprise-level indicators
        enterprise_keywords = [
            'enterprise', 'large-scale', 'production', 'deployment', 'scalable',
            'multi-platform', 'comprehensive system', 'full-stack', 'architecture'
        ]
        
        # Complex task indicators
        complex_keywords = [
            'machine learning', 'ai model', 'deep learning', 'neural network',
            'data analysis', 'statistical analysis', 'research paper', 'comprehensive',
            'multiple datasets', 'web scraping', 'api integration', 'database'
        ]
        
        # Medium complexity indicators
        medium_keywords = [
            'analyze', 'build', 'create', 'develop', 'implement', 'design',
            'application', 'tool', 'script', 'visualization', 'report'
        ]
        
        word_count = len(task_description.split())
        
        if any(keyword in task_lower for keyword in enterprise_keywords) or word_count > 100:
            return TaskComplexity.ENTERPRISE
        elif any(keyword in task_lower for keyword in complex_keywords) or word_count > 50:
            return TaskComplexity.COMPLEX
        elif any(keyword in task_lower for keyword in medium_keywords) or word_count > 20:
            return TaskComplexity.MEDIUM
        else:
            return TaskComplexity.SIMPLE

class ResilientAgent:
    """Enhanced agent wrapper with resilient execution"""
    
    def __init__(self, agent, llm_config: ResilientLLMConfig):
        self.agent = agent
        self.llm_config = llm_config
        
    def __getattr__(self, name):
        return getattr(self.agent, name)
        
    def generate_reply(self, *args, **kwargs):
        """Generate reply with resilient error handling"""
        return self.llm_config.execute_with_retry(
            self.agent.generate_reply, *args, **kwargs
        )

class EnhancedAutoAgentBuilder:
    """
    Enhanced AutoGen agent builder for tasks of all sizes
    """
    
    def __init__(self, llm_config: ResilientLLMConfig):
        self.llm_config = llm_config
        
    def analyze_task_and_build_agents(self, task_description: str) -> List:
        """
        Analyze task complexity and build appropriate agents
        """
        
        # Analyze task complexity
        complexity = TaskComplexityAnalyzer.analyze_complexity(task_description)
        logger.info(f"📊 Task complexity assessed as: {complexity.value.upper()}")
        
        # Get agent specifications based on complexity
        if complexity in [TaskComplexity.ENTERPRISE, TaskComplexity.COMPLEX]:
            return self._build_complex_agents(task_description, complexity)
        else:
            return self._build_simple_agents(task_description, complexity)
            
    def _build_complex_agents(self, task_description: str, complexity: TaskComplexity) -> List:
        """Build agents for complex/enterprise tasks"""
        
        print(f"🏗️ Building agent team for {complexity.value} task...")
        
        # Determine number of agents based on complexity
        if complexity == TaskComplexity.ENTERPRISE:
            max_agents = 7
            analysis_rounds = 2
        else:
            max_agents = 5
            analysis_rounds = 1
            
        agents = []
        
        # Use LLM to design agents
        try:
            agent_specs = self._get_agent_specifications(task_description, max_agents)
            
            for spec in agent_specs.get('agents', []):
                agent = self._create_agent_from_spec(spec, task_description)
                if agent:
                    agents.append(agent)
                    
        except Exception as e:
            logger.warning(f"LLM agent design failed: {e}. Using fallback design.")
            agents = self._create_fallback_complex_agents(task_description)
            
        # Add coordination agents for complex tasks
        if complexity == TaskComplexity.ENTERPRISE:
            agents.extend(self._create_coordination_agents(task_description))
            
        return agents
        
    def _build_simple_agents(self, task_description: str, complexity: TaskComplexity) -> List:
        """Build agents for simple/medium tasks"""
        
        print(f"🔧 Building streamlined agent team for {complexity.value} task...")
        
        try:
            max_agents = 3 if complexity == TaskComplexity.MEDIUM else 2
            agent_specs = self._get_agent_specifications(task_description, max_agents)
            
            agents = []
            for spec in agent_specs.get('agents', []):
                agent = self._create_agent_from_spec(spec, task_description)
                if agent:
                    agents.append(agent)
                    
            return agents
            
        except Exception as e:
            logger.warning(f"LLM agent design failed: {e}. Using fallback design.")
            return self._create_fallback_simple_agents(task_description)
            
    def _get_agent_specifications(self, task_description: str, max_agents: int) -> Dict:
        """Get agent specifications from LLM"""
        
        # Create temporary analyzer
        base_analyzer = autogen.AssistantAgent(
            name="TaskAnalyzer",
            system_message=f"""You are an expert at analyzing tasks and designing multi-agent systems.

            Design {max_agents} or fewer specialized agents for the given task.
            
            Respond with ONLY a JSON object in this format:
            {{
                "agents": [
                    {{
                        "name": "AgentName",
                        "role": "Brief role description",
                        "system_message": "Detailed system message",
                        "capabilities": ["capability1", "capability2"],
                        "needs_coding": true/false
                    }}
                ]
            }}
            
            Make each agent highly specialized with distinct roles.
            Include capabilities like: research, analysis, coding, writing, coordination, validation.
            Set needs_coding to true for agents that need to execute code.
            DO NOT include any text outside the JSON object.""",
            llm_config=self.llm_config.get_config()
        )
        
        analyzer = ResilientAgent(base_analyzer, self.llm_config)
        
        user_proxy = autogen.UserProxyAgent(
            name="TempUser",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=1,
            code_execution_config=False
        )
        
        analysis_prompt = f"""
        Analyze this task and design specialized agents:
        
        TASK: {task_description}
        
        Design agents with complementary skills. Respond with ONLY the JSON object.
        """
        
        # Get response
        user_proxy.initiate_chat(analyzer, message=analysis_prompt, max_turns=1)
        last_message = user_proxy.chat_messages[analyzer.agent][-1]["content"]
        
        # Extract and parse JSON
        json_start = last_message.find('{')
        json_end = last_message.rfind('}') + 1
        
        if json_start != -1 and json_end != -1:
            json_str = last_message[json_start:json_end]
            return json.loads(json_str)
        else:
            raise ValueError("No valid JSON found in response")
            
    def _create_agent_from_spec(self, spec: Dict, task_description: str):
        """Create agent from specification"""
        
        enhanced_message = f"""
        TASK CONTEXT: {task_description}
        
        ROLE: {spec['role']}
        
        {spec['system_message']}
        
        Your capabilities: {', '.join(spec.get('capabilities', []))}
        
        Work collaboratively and efficiently with other agents.
        Be thorough but respect API rate limits.
        """
        
        try:
            if spec.get('needs_coding', False):
                base_agent = autogen.UserProxyAgent(
                    name=spec['name'],
                    human_input_mode="NEVER",
                    max_consecutive_auto_reply=8,
                    code_execution_config={
                        "work_dir": f"workspace_{spec['name'].lower()}",
                        "use_docker": False
                    },
                    system_message=enhanced_message
                )
                return base_agent
            else:
                base_agent = autogen.AssistantAgent(
                    name=spec['name'],
                    system_message=enhanced_message,
                    llm_config=self.llm_config.get_config()
                )
                return ResilientAgent(base_agent, self.llm_config)
                
        except Exception as e:
            logger.error(f"Failed to create agent {spec.get('name', 'Unknown')}: {e}")
            return None
            
    def _create_coordination_agents(self, task_description: str) -> List:
        """Create coordination agents for enterprise tasks"""
        
        project_manager = autogen.AssistantAgent(
            name="ProjectManager",
            system_message=f"""You are the project manager for: {task_description}
            
            Responsibilities:
            - Oversee overall project progress
            - Coordinate between different agent teams
            - Ensure deliverables meet requirements
            - Make high-level decisions
            - Provide status updates and summaries
            
            Keep the project on track and ensure quality outcomes.""",
            llm_config=self.llm_config.get_config()
        )
        
        quality_assurance = autogen.AssistantAgent(
            name="QualityAssurance",
            system_message=f"""You are the quality assurance specialist for: {task_description}
            
            Responsibilities:
            - Review all outputs for quality and accuracy
            - Identify potential issues or improvements
            - Ensure consistency across deliverables
            - Validate that requirements are met
            - Suggest optimizations
            
            Maintain high standards and attention to detail.""",
            llm_config=self.llm_config.get_config()
        )
        
        return [
            ResilientAgent(project_manager, self.llm_config),
            ResilientAgent(quality_assurance, self.llm_config)
        ]
        
    def _create_fallback_complex_agents(self, task_description: str) -> List:
        """Fallback agents for complex tasks"""
        
        agents = []
        
        # Research specialist
        research_agent = autogen.AssistantAgent(
            name="ResearchSpecialist",
            system_message=f"You are a research specialist for: {task_description}. Focus on gathering information, analyzing data, and providing insights.",
            llm_config=self.llm_config.get_config()
        )
        agents.append(ResilientAgent(research_agent, self.llm_config))
        
        # Technical implementer
        tech_agent = autogen.UserProxyAgent(
            name="TechnicalImplementer",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=10,
            code_execution_config={
                "work_dir": "technical_workspace",
                "use_docker": False
            },
            system_message=f"You handle technical implementation for: {task_description}. Write code, create tools, and execute technical solutions."
        )
        agents.append(tech_agent)
        
        # Analyst
        analysis_agent = autogen.AssistantAgent(
            name="AnalysisExpert",
            system_message=f"You are an analysis expert for: {task_description}. Provide detailed analysis, insights, and recommendations.",
            llm_config=self.llm_config.get_config()
        )
        agents.append(ResilientAgent(analysis_agent, self.llm_config))
        
        return agents
        
    def _create_fallback_simple_agents(self, task_description: str) -> List:
        """Fallback agents for simple tasks"""
        
        primary_agent = autogen.AssistantAgent(
            name="PrimaryAgent",
            system_message=f"You are the primary agent for: {task_description}. Handle the main task efficiently and effectively.",
            llm_config=self.llm_config.get_config()
        )
        
        return [ResilientAgent(primary_agent, self.llm_config)]

# Main execution
def main():
    print("=" * 70)
    print("🚀 ENHANCED AUTOGEN INTELLIGENT AGENT BUILDER")
    print("=" * 70)
    print("Advanced multi-agent system that automatically scales for any task size!")
    print("\n✨ KEY FEATURES:")
    print("• Intelligent task complexity analysis")
    print("• Automatic rate limiting with dynamic adjustment")
    print("• Resilient error handling and recovery")
    print("• Scalable from simple tasks to enterprise projects")
    print("• Smart agent design based on task requirements")
    
    print("\n📋 TASK EXAMPLES:")
    print("🔸 SIMPLE: 'Summarize a research topic'")
    print("🔸 MEDIUM: 'Analyze a dataset and create visualizations'")
    print("🔸 COMPLEX: 'Build a machine learning model for prediction'")
    print("🔸 ENTERPRISE: 'Design and implement a full-stack web application'")
    
    print("\n💡 RATE LIMITING:")
    print("• Automatically detects and handles API limits")
    print("• Dynamic adjustment based on success/failure rates")
    print("• Intelligent retry with exponential backoff")
    
    print("-" * 70)
    
    # Get user input
    building_task = input("\n📝 Describe your task (any complexity level):\n> ").strip()
    
    if not building_task:
        print("No task provided. Using sample task...")
        building_task = "Research current trends in artificial intelligence and create a comprehensive analysis report."
    
    print(f"\n🎯 TASK: {building_task}")
    print("=" * 70)
    
    try:
        # Detect if user has paid tier (you can modify this detection logic)
        is_paid_tier = input("\n💳 Are you using a paid API tier? (y/n): ").lower().startswith('y')
        
        # Initialize components
        rate_manager = RateLimitManager(
            base_rpm=15 if is_paid_tier else 8,
            is_paid_tier=is_paid_tier
        )
        
        llm_config = ResilientLLMConfig({
            "config_list": [{
                'model': 'gemini-2.0-flash-exp',
                'api_key': gemini_api_key,
                'api_type': 'google'
            }],
            "seed": 42,
            "temperature": 0.7
        }, rate_manager)
        
        # Build agents
        builder = EnhancedAutoAgentBuilder(llm_config)
        agent_list = builder.analyze_task_and_build_agents(building_task)
        
        print(f"\n✅ Successfully created {len(agent_list)} specialized agents!")
        print("\n🤖 Your AI-designed team:")
        for i, agent in enumerate(agent_list):
            agent_name = getattr(agent, 'name', getattr(agent, 'agent', agent).name)
            print(f"  {i+1}. {agent_name}")
        
        # Determine conversation parameters based on team size
        max_rounds = min(30, max(10, len(agent_list) * 4))
        
        # Create group chat
        base_agents = []
        for agent in agent_list:
            if hasattr(agent, 'agent'):
                base_agents.append(agent.agent)
            else:
                base_agents.append(agent)
        
        group_chat = autogen.GroupChat(
            agents=base_agents,
            messages=[],
            max_round=max_rounds,
            speaker_selection_method="auto"
        )
        
        base_manager = autogen.GroupChatManager(
            groupchat=group_chat,
            llm_config=llm_config.get_config()
        )
        manager = ResilientAgent(base_manager, llm_config)
        
        print(f"\n🎬 Starting intelligent multi-agent collaboration...")
        print(f"📊 Max conversation rounds: {max_rounds}")
        print(f"⚡ Current rate limit: {rate_manager.get_current_limit()} RPM")
        print("=" * 70)
        
        # Start execution
        start_time = time.time()
        
        first_agent = base_agents[0]
        first_agent.initiate_chat(
            manager,
            message=f"""Team, let's efficiently complete this task: {building_task}

Please coordinate your specialized skills to deliver exceptional results.
Work smart, stay focused, and leverage each team member's expertise."""
        )
        
        # Execution summary
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 70)
        print("📊 EXECUTION SUMMARY")
        print("=" * 70)
        print(f"⏱️  Total execution time: {duration:.1f} seconds")
        print(f"🔄 API requests made: {rate_manager.success_count}")
        print(f"❌ Errors encountered: {rate_manager.error_count}")
        print(f"📈 Final rate limit: {rate_manager.get_current_limit()} RPM")
        print("✅ Task completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Execution interrupted by user.")
        
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Verify your API key is correct and active")
        print("2. Check internet connectivity")
        print("3. Ensure sufficient API quota/credits")
        print("4. Try with a simpler task description")
        print("5. Consider upgrading to paid tier for higher limits")
        
        if "quota" in str(e).lower():
            print("\n💳 QUOTA ISSUE: Check your API billing and usage limits")
        elif "429" in str(e):
            print("\n⏳ RATE LIMIT: The system will automatically handle this in retry")

if __name__ == "__main__":
    main()