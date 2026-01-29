# ai_services.py
import os
import logging
import json
import time
from typing import List, Dict, Any
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class AIEstimator:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
            
        self.client = genai.Client(api_key=api_key)
        self.model_id = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

    def estimate_task(self, task_description: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Calls Gemini API to get a structured task estimation."""
        
        prompt = f"""
        You are a software project management assistant specialized in Kanban-based workflows.
        Analyze the task below and return a STRICTLY VALID JSON response.
        
        TASK DESCRIPTION:
        {task_description}

        Return JSON in this EXACT format:
        {{
            "title": "Short action-based title (3-6 words, start with verb like Fix, Add, Update, Create)",
            "estimated_time": "string (e.g., '2 days', '1 week', '3 weeks')",
            "priority": "string (Low/Medium/High)",
            "complexity_level": "string (Low/Medium/High)",
            "dependencies": ["array of prerequisite tasks or systems"],
            "required_access": [
                "Specific access requirement 1 (e.g., 'GitHub Repository Write Access')",
                "Specific access requirement 2 (e.g., 'AWS Lambda Deployment Console')",
                "Specific access requirement 3 (e.g., 'PostgreSQL Database Admin Rights')"
            ],
            "suggested_labels": ["array", "of", "labels"],
            "reasoning": "MUST BE IN THIS EXACT FORMAT (see below)"
        }}
        
        CRITICAL: The "reasoning" field MUST follow this EXACT structure:
        
        "Phase 1: Technical Breakdown
Overview: [Write 3-4 concise technical sentences describing the approach, architecture, or key technologies involved. Be specific about the technical stack and implementation strategy.]

Phase 1: [First milestone name]
- [Specific task 1]
- [Specific task 2]
- [Specific task 3]

Phase 2: [Second milestone name]
- [Specific task 1]
- [Specific task 2]
- [Specific task 3]

Phase 3: [Third milestone name]
- [Specific task 1]
- [Specific task 2]
- [Specific task 3]"

        EXAMPLE of correct "reasoning" format:
        "Phase 1: Technical Breakdown
Overview: Relational SQL database with API-driven lead ingestion and AI intent-scoring. PostgreSQL/Supabase backend with REST API webhooks for multi-channel integration. LLM-powered qualification engine for automated lead scoring.

Phase 1: Setup PostgreSQL/Supabase DB and multi-channel API webhooks
- Configure PostgreSQL database schema with lead tracking tables
- Set up Supabase authentication and row-level security
- Create API webhook endpoints for lead ingestion from multiple channels

Phase 2: Deploy LLM-agent for lead qualification and scoring
- Integrate OpenAI/Claude API for natural language intent analysis
- Implement automated lead scoring algorithm based on interaction patterns
- Create qualification workflow with automated triggers and notifications

Phase 3: Launch Next.js dashboard for sales status management
- Build responsive dashboard UI with real-time lead status updates
- Implement advanced filtering, search, and sorting functionality
- Deploy production environment with monitoring and analytics"

        MANDATORY REQUIREMENTS:
        1. Overview MUST be 3-4 technical sentences describing the approach
        2. MUST have exactly 3 phases (Phase 1, Phase 2, Phase 3)
        3. Each phase MUST have 3 specific, actionable tasks with dash bullets (-)
        4. Use proper line breaks between sections
        5. Be specific to the task: "{task_description}"
        
        IMPORTANT for required_access:
        - Be specific about exact access needed for THIS TASK
        - Include service/tool name (GitHub, AWS, PostgreSQL, Slack, Telegram, etc.)
        - Specify access type (Read, Write, Admin, Console, etc.)
        - Examples:
          * "GitHub Repository Write Access"
          * "AWS Lambda Deployment Console"
          * "PostgreSQL Database Admin Rights"
          * "Slack Workspace Admin Permissions"
          * "Telegram BotFather Access"
          * "OAuth Provider Configuration Panel"
        
        Analyze the task and provide realistic, practical estimates.
        """
        
        try:
            # Configure generation with parameters
            generation_config = types.GenerateContentConfig(
                temperature=1.0,
                top_p=0.95,
                top_k=40,
                max_output_tokens=2048,
            )
            
            # Retry logic for 503 errors
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=self.model_id,
                        contents=prompt,
                        config=generation_config
                    )
                    break
                    
                except Exception as e:
                    if "503" in str(e) or "UNAVAILABLE" in str(e):
                        if attempt < max_retries - 1:
                            logger.warning(f"Attempt {attempt + 1} failed with 503, retrying in {retry_delay}s...")
                            time.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            raise
                    else:
                        raise
            
            # Parse JSON from response
            response_text = response.text.strip()
            
            logger.info(f"Raw AI Response for task '{task_description[:50]}...': {response_text[:200]}...")
            
            # Remove markdown code blocks
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            try:
                estimate_data = json.loads(response_text)
                
                # Ensure required_access is always an array
                if 'required_access' in estimate_data:
                    if isinstance(estimate_data['required_access'], str):
                        estimate_data['required_access'] = [estimate_data['required_access']]
                
                logger.info(f"Successfully parsed estimate for: {task_description[:50]}...")
                
                return {
                    "success": True,
                    "title": estimate_data.get("title", ""),
                    **estimate_data
                }
                
            except json.JSONDecodeError as je:
                logger.warning(f"Failed to parse JSON: {je}. Response: {response_text[:200]}")
                # Fallback with correct format
                return {
                    "success": True,
                    "title": "Task Needs Analysis",
                    "estimated_time": "1 week",
                    "priority": "Medium",
                    "complexity_level": "Medium",
                    "dependencies": ["Initial project setup"],
                    "required_access": [
                        "Development Environment Access",
                        "Version Control System (GitHub/GitLab)",
                        "Testing Environment"
                    ],
                    "suggested_labels": ["feature", "development"],
                    "reasoning": f"""Phase 1: Technical Breakdown
                Overview: {task_description[:200]}. Standard development workflow with modern tech stack. Requires environment setup, implementation, and deployment phases.

                Phase 1: Requirements Analysis and Setup
                - Review task requirements and define scope
                - Set up development environment and tools
                - Create project structure and initial configuration

                Phase 2: Core Implementation
                - Implement main functionality according to specifications
                - Write comprehensive unit and integration tests
                - Conduct code review and refactoring

                Phase 3: Testing and Deployment
                - Perform end-to-end testing in staging environment
                - Create deployment documentation and runbooks
                - Deploy to production with monitoring setup"""
                                }
                            
        except Exception as e:
            logger.error(f"Gemini API Error: {str(e)}")
            # Fallback with correct format
            return {
                "success": False,
                "error": f"AI Generation failed: {str(e)}",
                "title": "Manual Review Required",
                "estimated_time": "Unknown",
                "priority": "Medium",
                "complexity_level": "Medium",
                "dependencies": ["Requirements gathering needed"],
                "required_access": ["To be determined"],
                "suggested_labels": ["needs-analysis"],
                "reasoning": """Phase 1: Technical Breakdown
Overview: AI estimation service temporarily unavailable. Manual technical review required to assess scope, dependencies, and implementation approach.

Phase 1: Requirements Gathering
- Conduct stakeholder meetings to clarify requirements
- Document technical specifications and constraints
- Identify system dependencies and integration points

Phase 2: Technical Planning and Design
- Create detailed system architecture design
- Define API contracts and data models
- Estimate resource requirements and timeline

Phase 3: Implementation Strategy
- Break down work into manageable sprints
- Assign team members and allocate resources
- Set up monitoring and quality assurance processes"""
            }
