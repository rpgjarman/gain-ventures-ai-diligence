import os
import asyncio
import requests
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
from typing import Dict, Any
import json

class ResearchAgent:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    async def research_company(self, company_data) -> Dict[str, Any]:
        """Conduct comprehensive company research"""
        
        research_results = {
            "company_name": company_data.company_name,
            "website": company_data.website,
            "basic_info": {},
            "team_info": {},
            "product_info": {},
            "market_info": {},
            "financial_info": {},
            "news_mentions": [],
            "social_presence": {}
        }
        
        # Scrape company website
        website_data = await self._scrape_website(company_data.website)
        research_results["basic_info"] = website_data
        
        # Search for additional information
        search_data = await self._web_search(company_data.company_name)
        research_results["news_mentions"] = search_data.get("news", [])
        research_results["market_info"] = search_data.get("market", {})
        
        # Get team information
        team_data = await self._research_team(company_data.company_name)
        research_results["team_info"] = team_data
        
        return research_results
    
    async def _scrape_website(self, url: str) -> Dict[str, Any]:
        """Scrape company website for basic information"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract key information
            title = soup.find('title')
            meta_description = soup.find('meta', attrs={'name': 'description'})
            
            # Find about section
            about_text = self._extract_about_section(soup)
            
            return {
                "title": title.text.strip() if title else "",
                "description": meta_description.get('content', '') if meta_description else "",
                "about": about_text,
                "url": url
            }
            
        except Exception as e:
            return {"error": str(e), "url": url}
    
    def _extract_about_section(self, soup) -> str:
        """Extract about/description text from website"""
        about_selectors = [
            'section[class*="about"]',
            'div[class*="about"]',
            '.hero-content',
            '.hero-text',
            'main p',
            '.description'
        ]
        
        for selector in about_selectors:
            elements = soup.select(selector)
            if elements:
                text = ' '.join([elem.get_text().strip() for elem in elements[:3]])
                if len(text) > 50:
                    return text[:1000]
        
        # Fallback: get first few paragraphs
        paragraphs = soup.find_all('p')
        if paragraphs:
            text = ' '.join([p.get_text().strip() for p in paragraphs[:5]])
            return text[:1000]
        
        return ""
    
    async def _web_search(self, company_name: str) -> Dict[str, Any]:
        """Search for company information online"""
        try:
            # Use OpenAI to generate search summary
            prompt = f"""
            Research the company "{company_name}" and provide a structured summary including:
            1. Recent news and press mentions
            2. Market position and competitors
            3. Funding history if available
            4. Key partnerships or customers
            
            Format as JSON with keys: news, market, funding, partnerships
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            # Parse JSON response
            try:
                return json.loads(response.choices[0].message.content)
            except:
                return {"summary": response.choices[0].message.content}
                
        except Exception as e:
            return {"error": str(e)}
    
    async def _research_team(self, company_name: str) -> Dict[str, Any]:
        """Research company team and founders"""
        try:
            prompt = f"""
            Research the founding team and key executives of "{company_name}".
            Focus on:
            1. Founder backgrounds and experience
            2. Previous companies or exits
            3. Educational background
            4. Relevant industry experience
            
            Format as JSON with founder details.
            """
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            try:
                return json.loads(response.choices[0].message.content)
            except:
                return {"summary": response.choices[0].message.content}
                
        except Exception as e:
            return {"error": str(e)}