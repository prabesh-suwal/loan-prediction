import json
import logging
from typing import Dict, Any, Optional
import openai
from openai import OpenAI

from app.config.settings import settings

logger = logging.getLogger(__name__)

class LLMExplainer:
    """LLM-based explanation service for loan decisions."""
    
    def __init__(self):
        self.client = None
        if settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
    
    def generate_explanation(
        self, 
        input_data: Dict[str, Any], 
        prediction_result: Dict[str, Any]
    ) -> str:
        """Generate human-readable explanation for loan decision."""
        
        if not self.client:
            return self._generate_rule_based_explanation(input_data, prediction_result)
        
        try:
            # Prepare prompt for LLM
            prompt = self._create_explanation_prompt(input_data, prediction_result)
            
            response = self.client.chat.completions.create(
                model=settings.llm_model_name,  # Fixed reference
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial analyst expert at explaining loan approval decisions. Provide clear, concise explanations that are easy to understand."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            explanation = response.choices[0].message.content.strip()
            return explanation
            
        except Exception as e:
            logger.error(f"LLM explanation failed: {e}")
            return self._generate_rule_based_explanation(input_data, prediction_result)
    
    def _create_explanation_prompt(
        self, 
        input_data: Dict[str, Any], 
        prediction_result: Dict[str, Any]
    ) -> str:
        """Create prompt for LLM explanation."""
        
        prompt = f"""
        Loan Application Analysis:
        
        Applicant Details:
        - Gender: {input_data.get('gender', 'N/A')}
        - Marital Status: {input_data.get('married', 'N/A')}
        - Education: {input_data.get('education', 'N/A')}
        - Self Employed: {input_data.get('self_employed', 'N/A')}
        - Dependents: {input_data.get('dependents', 'N/A')}
        - Property Area: {input_data.get('property_area', 'N/A')}
        
        Financial Information:
        - Applicant Income: ${input_data.get('applicant_income', 0):,.2f}
        - Co-applicant Income: ${input_data.get('coapplicant_income', 0):,.2f}
        - Loan Amount: ${input_data.get('loan_amount', 0):,.2f}
        - Loan Term: {input_data.get('loan_amount_term', 0)} months
        - Credit History: {'Good' if input_data.get('credit_history') == 1 else 'Poor'}
        
        AI Decision:
        - Loan Decision: {prediction_result.get('loan_decision')}
        - Risk Score: {prediction_result.get('risk_score')}/100
        - Risk Category: {prediction_result.get('risk_category')}
        - Recommendation: {prediction_result.get('recommendation')}
        - Confidence: {prediction_result.get('confidence_score', 0):.2%}
        
        Please provide a clear, professional explanation (2-3 sentences) for this loan decision that focuses on the key factors that influenced the outcome.
        """
        
        return prompt
    
    def _generate_rule_based_explanation(
        self, 
        input_data: Dict[str, Any], 
        prediction_result: Dict[str, Any]
    ) -> str:
        """Generate rule-based explanation as fallback."""
        
        decision = prediction_result.get('loan_decision')
        risk_score = prediction_result.get('risk_score', 0)
        
        # Calculate key metrics
        total_income = input_data.get('applicant_income', 0) + input_data.get('coapplicant_income', 0)
        emi = input_data.get('loan_amount', 0) / input_data.get('loan_amount_term', 1)
        emi_ratio = emi / total_income if total_income > 0 else 0
        
        explanation_parts = []
        
        if decision == "Yes":
            explanation_parts.append("Loan approved based on")
            
            if input_data.get('credit_history') == 1:
                explanation_parts.append("good credit history")
            
            if emi_ratio < 0.3:
                explanation_parts.append("manageable EMI burden")
            
            if total_income > 5000:
                explanation_parts.append("adequate income level")
                
        else:
            explanation_parts.append("Loan rejected due to")
            
            if input_data.get('credit_history') == 0:
                explanation_parts.append("poor credit history")
            
            if emi_ratio > 0.5:
                explanation_parts.append("high EMI-to-income ratio")
            
            if total_income < 3000:
                explanation_parts.append("insufficient income")
        
        # Risk assessment
        if risk_score > 70:
            explanation_parts.append("and high financial risk")
        elif risk_score < 30:
            explanation_parts.append("with low financial risk")
        
        if len(explanation_parts) == 1:
            return f"{explanation_parts[0]} standard eligibility criteria."
        
        base = explanation_parts[0]
        factors = ", ".join(explanation_parts[1:-1])
        last_factor = explanation_parts[-1]
        
        if len(explanation_parts) > 2:
            return f"{base} {factors}, and {last_factor}."
        else:
            return f"{base} {last_factor}."

