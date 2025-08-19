from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

# Import our custom agents and utilities
from agents.research_agent import ResearchAgent
from agents.web3_agent import Web3Agent
from agents.diligence_agent import DiligenceAgent
from utils.airtable_client import AirtableClient
from utils.email_client import EmailClient

# Load environment variables
load_dotenv()

app = FastAPI(title="Gain Ventures AI Diligence", version="1.0.0")

class CompanyData(BaseModel):
    company_name: str
    website: str
    external_id: str
    industry: str
    one_liner: str = ""
    description: str = ""

# Initialize clients and agents
airtable = AirtableClient()
email_client = EmailClient()
research_agent = ResearchAgent()
web3_agent = Web3Agent()
diligence_agent = DiligenceAgent()

@app.post("/research/company")
async def trigger_research(company: CompanyData, background_tasks: BackgroundTasks):
    """Trigger AI research for a company"""
    
    # Add background task for processing
    background_tasks.add_task(process_company_research, company)
    
    return {
        "message": f"Research started for {company.company_name}",
        "external_id": company.external_id,
        "status": "processing"
    }

async def process_company_research(company: CompanyData):
    """Background task to process company research"""
    
    try:
        print(f"Starting research for {company.company_name}")
        
        # Step 1: Update status in Airtable
        await airtable.update_record(company.external_id, {
            "Stage": "Initial Research",
            "Diligence Status": "In Progress",
            "Last Updated": datetime.now().strftime("%m/%d/%Y, %I:%M %p")
        })
        
        # Step 2: General company research
        print("Conducting company research...")
        research_data = await research_agent.research_company(company)
        
        # Step 3: Web3-specific analysis
        print("Conducting Web3 analysis...")
        web3_analysis = await web3_agent.analyze_web3_company(company, research_data)
        
        # Step 4: Generate diligence report
        print("Generating diligence report...")
        diligence_report = await diligence_agent.generate_report(
            company, research_data, web3_analysis
        )
        
        # Step 5: Update Airtable with results
        print("Updating Airtable...")
        await airtable.update_record(company.external_id, {
            "Stage": "Partner Review",
            "Diligence Status": "Complete", 
            "AI Recommendation": diligence_report.get("investment_recommendation", "Monitor"),
            "Last Updated": datetime.now().strftime("%m/%d/%Y, %I:%M %p")
        })
        
        # Step 6: Send email to partners
        print("Sending email report...")
        await email_client.send_diligence_report(
            company.company_name,
            diligence_report.get("pdf_path", ""),
            diligence_report.get("executive_summary", "Summary not available")
        )
        
        print(f"Successfully completed research for {company.company_name}")
        
    except Exception as e:
        print(f"Error processing {company.company_name}: {str(e)}")
        
        # Update Airtable with error status
        try:
            await airtable.update_record(company.external_id, {
                "Stage": "New Lead",
                "Diligence Status": "Failed",
                "AI Recommendation": "Error - Review Manually",
                "Last Updated": datetime.now().strftime("%m/%d/%Y, %I:%M %p")
            })
        except:
            print("Failed to update error status in Airtable")

@app.get("/")
async def root():
    return {
        "message": "Gain Ventures AI Diligence API", 
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/test/airtable")
async def test_airtable():
    """Test Airtable connection"""
    try:
        records = await airtable.get_records_by_status("Pending")
        return {
            "status": "success",
            "records_found": len(records),
            "message": "Airtable connection working"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)