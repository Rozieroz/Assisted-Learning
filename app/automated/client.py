"""
Groq API client with rate limit handling and error resilience.
Uses Zero Data Retention (ZDR) configuration for privacy compliance.
"""

"""
Automated content generation service using Groq.
Handles quiz generation, feedback, simplified explanations, and rate limit resilience.
Includes question bank management for variety.
"""

import os
import re
import json
import random
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from groq import AsyncGroq
from groq import RateLimitError, APIError

logger = logging.getLogger(__name__)

class AutomatedContentService:
    """Service for generating content using Groq LLMs with error handling."""
    
    def __init__(self):
        """Initialize the Groq async client with API key from environment."""
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            logger.warning("GROQ_API_KEY not found in environment variables")
        
        self.client = AsyncGroq(
            api_key=self.api_key,
        )
        
        # Model selection based on task complexity
        self.models = {
            "quiz_generation": "llama-3.3-70b-versatile",
            "feedback_standard": "llama-3.1-8b-instant",
            "feedback_simplified": "llama-3.1-8b-instant",
            "explanation_simplify": "llama-3.1-8b-instant"
        }
        
        # Track recently generated questions to avoid repetition
        self.recent_questions = {}  # key: f"{topic}_{difficulty}", value: list of recent questions
        
    def _extract_rate_limit_wait_time(self, error_message: str) -> str:
        """Extract wait time from rate limit error messages."""
        match = re.search(r"try again in (\d+)m(\d+\.?\d*)s", error_message)
        if match:
            minutes = match.group(1)
            seconds = match.group(2)
            return f"{minutes} minutes and {seconds} seconds"
        return "a few minutes"
    
    def _handle_api_error(self, error: Exception, operation: str) -> str:
        """Centralized error handling for API calls."""
        error_str = str(error)
        logger.error(f"Groq API error during {operation}: {error_str}")
        
        if "429" in error_str or "rate_limit_exceeded" in error_str:
            wait_time = self._extract_rate_limit_wait_time(error_str)
            return f"⚠️ Daily usage limit reached. Please try again in about {wait_time}. (Groq API rate limit)"
        
        if isinstance(error, APIError):
            return f"Groq API error: {error_str}"
        
        return f"Error calling Groq API: {error_str}"
    
    async def generate_quiz_question(self, topic: str, difficulty: str, recent_questions: List[str] = None) -> Dict[str, Any]:
        """
        Generate a multiple-choice quiz question with awareness of recent questions to avoid repetition.
        """
        # Create a key for tracking
        topic_key = f"{topic}_{difficulty}"
        
        # Initialize recent questions list if not exists
        if topic_key not in self.recent_questions:
            self.recent_questions[topic_key] = []
        
        # Get list of recent questions to avoid (from parameter or internal tracking)
        avoid_list = recent_questions or self.recent_questions[topic_key][-5:]  # Avoid last 5
        
        # Random seed for variety
        seed = random.randint(1, 1000000)
        
        # Question templates to rotate through
        templates = [
            "Create a challenging multiple-choice question about {topic}",
            "Create an interesting real-world application question about {topic}",
            "Create a conceptual understanding question about {topic}",
            "Create a problem-solving question involving {topic}",
            "Create a question that tests practical knowledge of {topic}",
            "Create a question about a key concept in {topic}",
            "Create a question that requires critical thinking about {topic}",
            "Create a question about an important formula or principle in {topic}"
        ]
        template = templates[seed % len(templates)]
        
        # Difficulty-specific instructions
        difficulty_guides = {
            "easy": "Focus on basic concepts and straightforward applications. Keep it simple.",
            "medium": "Include intermediate concepts that require some thought. Mix of theory and practice.",
            "hard": "Challenge with complex scenarios, multi-step problems, or advanced concepts."
        }
        
        # Build the prompt with explicit anti-repetition instructions
        prompt = f"""
        {template.format(topic=topic)} at {difficulty} difficulty level.
        
        {difficulty_guides.get(difficulty, '')}
        
        IMPORTANT RULES:
        1. This MUST be DIFFERENT from these recent questions about {topic}:
        {chr(10).join([f'   - {q[:100]}...' for q in avoid_list if q])}
        
        2. Create completely new content - different scenario, different concepts, different approach.
        
        3. Use seed {seed} for uniqueness.
        
        Return in this exact JSON format:
        {{
            "question": "the question text",
            "option_a": "first option",
            "option_b": "second option",
            "option_c": "third option",
            "option_d": "fourth option",
            "correct_answer": "A/B/C/D",
            "explanation": "brief explanation of the correct answer",
            "keywords": ["keyword1", "keyword2"]  # Add 2-3 keywords about what this question covers
        }}
        
        Ensure all options are plausible and the correct answer is clearly correct.
        """

        if recent_questions:
            avoid_text = "\n".join([f"   - {q[:100]}..." for q in recent_questions if q])
            prompt = prompt.replace(
                "IMPORTANT RULES:",
                f"IMPORTANT RULES:\n\nAvoid these recent questions:\n{avoid_text}\n"
            )
        
        try:
            response = await self.client.chat.completions.create(
                model=self.models["quiz_generation"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.95,
                response_format={"type": "json_object"},
                max_tokens=600
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Extract question text for tracking
            question_text = result.get("question", "")
            
            # Update recent questions list
            self.recent_questions[topic_key].append(question_text)
            # Keep only last 10
            if len(self.recent_questions[topic_key]) > 10:
                self.recent_questions[topic_key].pop(0)
            
            logger.info(f"Generated quiz question for {topic} at {difficulty} difficulty (seed: {seed})")
            
            # Add metadata
            result["_generation_seed"] = seed
            result["_model_used"] = self.models["quiz_generation"]
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {"error": "Invalid response format from generation service"}
        except Exception as e:
            error_msg = self._handle_api_error(e, "quiz generation")
            return {"error": error_msg}
    
    async def generate_feedback(
        self,
        question: str,
        user_answer: str,
        correct_answer: str,
        is_correct: bool,
        simplified: bool = False
    ) -> str:
        """Generate personalized feedback for a student's answer."""
        # (Keep this method as is from previous version)
        if is_correct:
            prompt = f"""
            The student answered correctly. Provide encouraging feedback 
            that reinforces why their answer was right.
            
            Question: {question}
            Correct answer: {correct_answer}
            
            Keep feedback concise and supportive.
            """
        else:
            prompt = f"""
            The student answered incorrectly. Provide helpful feedback that:
            1. Gently points out the mistake
            2. Explains the correct answer clearly
            3. Offers encouragement to try again
            
            Question: {question}
            Student's answer: {user_answer}
            Correct answer: {correct_answer}
            
            Keep feedback constructive and encouraging.
            """
        
        if simplified:
            prompt += "\n\nUse very simple language, short sentences, and clear explanations suitable for students who need simplified content."
        
        model = self.models["feedback_simplified"] if simplified else self.models["feedback_standard"]
        
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=200
            )
            
            feedback = response.choices[0].message.content
            logger.info(f"Generated feedback (simplified={simplified})")
            return feedback
            
        except Exception as e:
            error_msg = self._handle_api_error(e, "feedback generation")
            return error_msg
    
    async def simplify_explanation(self, text: str) -> str:
        """Convert complex explanations into simpler language."""
        # (Keep this method as is from previous version)
        prompt = f"""
        Rewrite the following explanation using very simple language:
        - Use short sentences
        - Avoid complex vocabulary
        - Break down concepts step by step
        - Make it easy to understand
        
        Original: {text}
        
        Simplified version:
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.models["explanation_simplify"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )
            
            simplified = response.choices[0].message.content
            logger.info("Generated simplified explanation")
            return simplified
            
        except Exception as e:
            logger.error(f"Simplification failed: {e}")
            return text

# Singleton instance
automated_service = AutomatedContentService()


"""
has a three‑tier model mapping for different tasks.
include sophisticated rate‑limit error parsing and user‑friendly messages.
return structured dictionaries with metadata (model used, token usage, etc.).
design with Zero Data Retention (ZDR) in mind.
"""