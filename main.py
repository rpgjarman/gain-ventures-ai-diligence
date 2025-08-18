from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import asyncio
import os
from dotenv import load_dotenv

from agents.research_agent import ResearchAgent
from agents.web3_agent import Web3Agent
from agents.diligence_agent import DiligenceAgent
from utils.airtable_client import AirtableClient
from utils.email_client import EmailClient

load_dotenv()

app = FastAPI(title="Gain Ventures AI Diligence", version="1.0.0")

class CompanyData(BaseModel):
    company_name: str
    website: str
    external_id: str
    industry: str
    one_liner: str = ""
    description: str = ""

# Initialize clients
airtable = AirtableClient()
email_client = EmailClient()
research_agent = ResearchAgent()
web3_agent = Web3Agent()
diligence_agent = DiligenceAgent()

@app.post("/research/company")
async def trigger_research(company: CompanyData, background_tasks: BackgroundTasks):
    """Trigger AI research for a company"""
    
    background_tasks.add_task(process_company_research, company)
    
    return {
        "message": f"Research started for {company.company_name}",
        "external_id": company.external_id,
        "status": "processing"
    }

async def process_company_research(company: CompanyData):
    """Background task to process company research"""
    
    try:
        # Update status in Airtable
        await airtable.update_record(company.external_id, {
            "Stage": "Initial Research",
            "Diligence Status": "In Progress"
        })
        
        # Step 1: General company research
        research_data = await research_agent.research_company(company)
        
        # Step 2: Web3-specific analysis
        web3_analysis = await web3_agent.analyze_web3_company(company, research_data)
        
        # Step 3: Generate diligence report
        diligence_report = await diligence_agent.generate_report(
            company, research_data, web3_analysis
        )
        
        # Step 4: Update Airtable with results
        await airtable.update_record(company.external_id, {
            "Stage": "Partner Review",
            "Diligence Status": "Complete", 
            "AI Recommendation": diligence_report["recommendation"],
            "Last Updated": datetime.now().strftime("%m/%d/%Y, %I:%M %p")
        })
        
        # Step 5: Send email to partners
        await email_client.send_diligence_report(
            company.company_name,
            diligence_report["pdf_path"],
            diligence_report["summary"]
        )
        
    except Exception as e:
        # Handle errors
        await airtable.update_record(company.external_id, {
            "Stage": "New Lead",
            "Diligence Status": "Failed",
            "AI Recommendation": "Error - Review Manually"
        })
        print(f"Error processing {company.company_name}: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Gain Ventures AI Diligence API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)