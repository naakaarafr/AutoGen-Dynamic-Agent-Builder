# AutoGen Dynamic Agent Builder

![AutoGen](https://img.shields.io/badge/AutoGen-Multi--Agent-blue)
![Gemini](https://img.shields.io/badge/Gemini-2.0--Flash-green)
![Python](https://img.shields.io/badge/Python-3.8+-yellow)
![License](https://img.shields.io/badge/License-MIT-red)

An intelligent multi-agent system that automatically designs and creates specialized AI agents based on your task requirements using Microsoft's AutoGen framework and Google's Gemini AI.

## 🌟 Features

- **🤖 Intelligent Agent Design**: Uses AI to automatically analyze tasks and create optimal agent teams
- **🎯 Dynamic Agent Creation**: Builds specialized agents with distinct roles and capabilities  
- **🔄 Multi-Agent Collaboration**: Coordinates multiple agents working together seamlessly
- **💡 Adaptive System**: Two implementation approaches for maximum flexibility
- **🛠️ Code Execution**: Agents can write and execute code when needed
- **📊 Task Analysis**: AI-powered task breakdown and agent role assignment

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key
- Git (for cloning the repository)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/naakaarafr/AutoGen-Dynamic-Agent-Builder.git
cd AutoGen-Dynamic-Agent-Builder
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

4. **Run the application**
```bash
# Option 1: Original AgentBuilder approach
python app.py

# Option 2: Custom AI-designed agents
python app_alternate.py
```

## 📁 Project Structure

```
AutoGen-Dynamic-Agent-Builder/
├── app.py                 # Original AutoGen AgentBuilder implementation
├── app_alternate.py       # Custom AI-powered agent designer
├── .env                   # Environment variables (create this)
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── agent_workspace/      # Directory for agent code execution
└── workspace/            # Alternative workspace directory
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Your Google Gemini API key | Yes |

### LLM Configuration

The system is configured to use Google's Gemini 2.0 Flash model:

```python
config_list = [
    {
        'model': 'gemini-2.0-flash-exp',
        'api_key': your_api_key,
        'api_type': 'google'
    }
]
```

## 🎮 Usage

### Basic Usage

1. **Start the application**
```bash
python app_alternate.py
```

2. **Describe your task** when prompted:
```
Please describe the task you want the agents to accomplish:
> Find and analyze recent machine learning papers on transformers
```

3. **Watch the magic happen**:
   - AI analyzes your task
   - Designs optimal agent roles
   - Creates specialized agents
   - Coordinates multi-agent collaboration

### Example Tasks

Here are some example tasks you can try:

- **📚 Research Tasks**: "Find and analyze academic papers from arxiv on quantum computing"
- **💻 Development Tasks**: "Build a web application with user authentication and database integration"
- **📊 Data Analysis**: "Analyze a dataset and create comprehensive data visualizations"
- **🌐 Web Scraping**: "Scrape e-commerce websites and generate market analysis reports"
- **💰 Trading Bots**: "Create a cryptocurrency trading bot with risk management"
- **📝 Content Creation**: "Research and write a comprehensive report on renewable energy trends"

## 🏗️ Architecture

### Two Implementation Approaches

#### 1. `app.py` - AutoGen AgentBuilder
- Uses AutoGen's built-in `AgentBuilder` class
- Automatically creates agents based on task description
- Fallback mechanisms for error handling
- Configuration saving for agent reuse

#### 2. `app_alternate.py` - Custom AI Designer
- Uses AI to analyze tasks and design agent teams
- More flexible and intelligent agent creation
- Dynamic role assignment and capability matching
- Enhanced coordination and collaboration

### Agent Types

The system creates various types of agents:

- **🎯 Task-Specific Agents**: Specialized for particular aspects of your task
- **💻 Coding Agents**: Can write and execute code (UserProxyAgent)
- **🤔 Analysis Agents**: Focus on research and analysis (AssistantAgent)
- **🎨 Creative Agents**: Handle content creation and writing
- **📊 Coordinator Agents**: Manage team collaboration and task completion

## 🔄 How It Works

### Step-by-Step Process

1. **Task Input**: User provides a natural language description of their task
2. **AI Analysis**: The system uses Gemini AI to analyze the task requirements
3. **Agent Design**: AI determines optimal agent roles, capabilities, and system messages
4. **Agent Creation**: Specialized agents are instantiated with appropriate configurations
5. **Group Formation**: Agents are organized into a collaborative group chat
6. **Task Execution**: Agents work together to complete the task
7. **Coordination**: A manager agent coordinates the conversation and ensures completion

### Agent Communication Flow

```
User Task → AI Analysis → Agent Design → Agent Creation → Group Chat → Task Execution
```

## 🛠️ Customization

### Modifying Agent Configuration

You can customize various aspects:

```python
# Adjust the number of agents
max_agents=4  # in app.py

# Modify conversation rounds
max_round=20  # in group chat configuration

# Change temperature for creativity
"temperature": 0.7  # in llm_config
```

### Adding New Capabilities

To extend the system:

1. **Custom Agent Types**: Create new agent classes with specific capabilities
2. **Enhanced Prompts**: Modify system messages for better performance
3. **Tool Integration**: Add external tools and APIs for agents to use
4. **Workspace Configuration**: Customize code execution environments

## 🔍 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `GEMINI_API_KEY not found` | Check your `.env` file and API key |
| `Agent building failed` | Verify internet connection and API accessibility |
| `Code execution errors` | Ensure proper workspace permissions |
| `JSON parsing errors` | Check if the AI response format is correct |

### Debug Mode

For debugging, you can:

1. **Enable verbose logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **Check agent configurations**:
```python
# Uncomment in app.py to save configurations
save_agent_configs(agent_configs)
```

3. **Monitor conversations**:
The system prints detailed logs of agent interactions.

## 📈 Performance Tips

- **Clear Task Descriptions**: More detailed tasks lead to better agent design
- **Reasonable Scope**: Break down very large tasks into smaller components
- **API Limits**: Be aware of Gemini API rate limits and quotas
- **Resource Management**: Monitor system resources during code execution

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/AutoGen-Dynamic-Agent-Builder.git

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # if available

# Run tests
python -m pytest tests/  # if tests are available
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Microsoft AutoGen**: For the amazing multi-agent framework
- **Google Gemini**: For the powerful AI capabilities
- **Open Source Community**: For inspiration and contributions

## 📞 Support

- **Issues**: Report bugs and feature requests on [GitHub Issues](https://github.com/naakaarafr/AutoGen-Dynamic-Agent-Builder/issues)
- **Discussions**: Join conversations on [GitHub Discussions](https://github.com/naakaarafr/AutoGen-Dynamic-Agent-Builder/discussions)
- **Documentation**: Check the [Wiki](https://github.com/naakaarafr/AutoGen-Dynamic-Agent-Builder/wiki) for detailed guides

## 🔮 Future Plans

- **🎨 Web Interface**: GUI for easier interaction
- **🔧 More LLM Support**: Integration with OpenAI, Claude, and other models
- **📊 Agent Analytics**: Performance monitoring and optimization
- **🌐 Cloud Deployment**: Easy deployment options
- **🔌 Plugin System**: Extensible architecture for custom tools

## 📊 Project Status

This project is actively maintained and under continuous development. Check the [changelog](CHANGELOG.md) for recent updates.

---

**⭐ If you find this project useful, please consider giving it a star on GitHub!**
