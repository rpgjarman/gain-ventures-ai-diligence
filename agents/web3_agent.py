import os
from openai import AsyncOpenAI
from typing import Dict, Any
import json

class Web3Agent:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.framework = self._load_web3_framework()
    
    def _load_web3_framework(self) -> str:
        """Load the Web3 investment framework"""
        try:
            with open('templates/web3_framework.txt', 'r') as f:
                return f.read()
        except FileNotFoundError:
            return self._default_framework()
    
    def _default_framework(self) -> str:
        """Default Web3 framework if file not found"""
        return """
        # Gain Ventures Web3 Investment Framework
        ## Focus Areas: DeFi, NFT, DAO, Infrastructure, Gaming
        ## Stage: Pre-seed to Series A
        ## Key Metrics: TVL, Active Users, Token Distribution
        """
    
    async def analyze_web3_company(self, company_data, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze company through Web3 investment lens"""
        
        analysis_prompt = f"""
        As a Web3 investment analyst, analyze this company using the following framework:
        
        {self.framework}
        
        Company Information:
        - Name: {company_data.company_name}
        - Website: {company_data.website}
        - Industry: {company_data.industry}
        - Description: {company_data.description}
        
        Research Data:
        {json.dumps(research_data, indent=2)}
        
        Provide a comprehensive Web3-focused analysis including:
        1. **Web3 Category Classification**: Which focus area does this fit?
        2. **Token Analysis**: Does it have tokens? Tokenomics assessment
        3. **Technology Stack**: Blockchain/protocol analysis
        4. **Competitive Landscape**: Similar Web3 projects
        5. **Metrics Evaluation**: Key Web3 metrics and traction
        6. **Risk Assessment**: Web3-specific risks (regulatory, technical, etc.)
        7. **Investment Thesis**: Why this could be a good/bad Web3 investment
        
        Format as structured JSON with clear sections.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.2,
                max_tokens=2000
            )
            
            analysis_text = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to structured text
            try:
                analysis_json = json.loads(analysis_text)
            except:
                analysis_json = {
                    "web3_analysis": analysis_text,
                    "category": self._extract_category(analysis_text),
                    "recommendation": self._extract_recommendation(analysis_text)
                }
            
            # Add framework scoring
            analysis_json["framework_score"] = await self._score_against_framework(
                company_data, research_data, analysis_json
            )
            
            return analysis_json
            
        except Exception as e:
            return {"error": str(e), "analysis": "Failed to complete Web3 analysis"}
    
    def _extract_category(self, analysis_text: str) -> str:
        """Extract Web3 category from analysis"""
        categories = ["DeFi", "NFT", "DAO", "Infrastructure", "GameFi", "Social", "Trading"]
        for category in categories:
            if category.lower() in analysis_text.lower():
                return category
        return "Other"
    
    def _extract_recommendation(self, analysis_text: str) -> str:
        """Extract investment recommendation"""
        text_lower = analysis_text.lower()
        if "strong buy" in text_lower or "highly recommend" in text_lower:
            return "Go"
        elif "avoid" in text_lower or "pass" in text_lower or "high risk" in text_lower:
            return "No-Go"
        else:
            return "Monitor"
    
    async def _score_against_framework(self, company_data, research_data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Score the company against Web3 framework criteria"""
        
        scoring_prompt = f"""
        Score this Web3 company against our investment framework on a scale of 1-10:
        
        Company: {company_data.company_name}
        Analysis: {json.dumps(analysis, indent=2)}
        
        Score these areas (1-10):
        1. Team Quality & Experience
        2. Technology Innovation
        3. Market Opportunity Size
        4. Tokenomics & Business Model
        5. Traction & Community
        6. Regulatory Risk (10 = low risk)
        7. Competitive Position
        8. Investment Fit (our thesis alignment)
        
        Provide scores as JSON: {{"team_score": X, "tech_score": X, ...}}
        Also include overall_score (average) and investment_recommendation ("Go", "No-Go", "Monitor")
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": scoring_prompt}],
                temperature=0.1
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {
                "error": str(e),
                "overall_score": 5.0,
                "investment_recommendation": "Monitor"
            }