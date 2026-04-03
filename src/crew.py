"""
ScholarForge CrewAI Crew
Multi-agent system for research, analysis, and report generation
"""
from crewai import Agent, Crew, Process, Task
from crewai_tools import tool
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize LLM
try:
    from langchain_openai import ChatOpenAI
    llm = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("LLM_MODEL", "gpt-4")
    )
except Exception as e:
    print(f"Warning: Could not initialize LLM: {e}")
    llm = None


# Define Tools
@tool
def research_tool(query: str) -> str:
    """Search and research information on a given topic"""
    return f"Research results for: {query}"


@tool
def analysis_tool(data: str) -> str:
    """Analyze research data and extract insights"""
    return f"Analysis of: {data}"


@tool  
def report_tool(content: str) -> str:
    """Generate formatted reports from analysis"""
    return f"Report generated from: {content}"


# Define Agents
researcher = Agent(
    role="Research Analyst",
    goal="Conduct thorough research on academic and professional topics",
    backstory="Expert researcher with deep knowledge across multiple domains",
    tools=[research_tool],
    verbose=True,
)

analyst = Agent(
    role="Data Analyst",
    goal="Analyze research data and identify key insights and patterns",
    backstory="Skilled analyst with expertise in data interpretation",
    tools=[analysis_tool],
    verbose=True,
)

report_writer = Agent(
    role="Report Writer",
    goal="Create comprehensive, well-structured reports from analysis",
    backstory="Professional writer specializing in academic and business reports",
    tools=[report_tool],
    verbose=True,
)


# Define Tasks
research_task = Task(
    description="Research the given topic thoroughly and compile findings",
    agent=researcher,
    expected_output="Comprehensive research findings with sources",
)

analysis_task = Task(
    description="Analyze the research findings and identify patterns",
    agent=analyst,
    expected_output="Key insights and analysis summary",
)

report_task = Task(
    description="Create a professional report from the analysis",
    agent=report_writer,
    expected_output="Formatted report ready for delivery",
)


# Create Crew
crew = Crew(
    agents=[researcher, analyst, report_writer],
    tasks=[research_task, analysis_task, report_task],
    process=Process.sequential,
    verbose=True,
)


def run_crew(topic: str) -> str:
    """Execute the crew for a given research topic"""
    results = crew.kickoff(inputs={"topic": topic})
    return results


if __name__ == "__main__":
    result = run_crew("Artificial Intelligence in Education")
    print(result)
