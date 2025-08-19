import os
from openai import AsyncOpenAI
from typing import Dict, Any
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

class DiligenceAgent:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.styles = getSampleStyleSheet()
    
    async def generate_report(self, company_data, research_data: Dict[str, Any], web3_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive diligence report"""
        
        report_data = {
            "company_name": company_data.company_name,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "executive_summary": "",
            "investment_recommendation": "",
            "key_findings": [],
            "risks": [],
            "opportunities": [],
            "next_steps": [],
            "scoring": web3_analysis.get("framework_score", {}),
            "raw_data": {
                "research": research_data,
                "web3_analysis": web3_analysis
            }
        }
        
        # Generate executive summary
        report_data["executive_summary"] = await self._generate_executive_summary(
            company_data, research_data, web3_analysis
        )
        
        # Generate structured findings
        structured_analysis = await self._generate_structured_analysis(
            company_data, research_data, web3_analysis
        )
        
        report_data.update(structured_analysis)
        
        # Generate PDF report
        pdf_path = await self._generate_pdf_report(report_data)
        report_data["pdf_path"] = pdf_path
        
        return report_data
    
    async def _generate_executive_summary(self, company_data, research_data: Dict[str, Any], web3_analysis: Dict[str, Any]) -> str:
        """Generate executive summary using AI"""
        
        summary_prompt = f"""
        Generate a concise executive summary (3-4 paragraphs) for this investment opportunity:
        
        Company: {company_data.company_name}
        Website: {company_data.website}
        Industry: {company_data.industry}
        
        Research Summary: {json.dumps(research_data, indent=2)[:1500]}
        Web3 Analysis: {json.dumps(web3_analysis, indent=2)[:1500]}
        
        Include:
        1. What the company does
        2. Key strengths and market opportunity
        3. Investment highlights
        4. Primary concerns or risks
        5. Clear recommendation (Go/No-Go/Monitor)
        
        Keep it executive-friendly and focused on investment decision-making.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": summary_prompt}],
                temperature=0.2,
                max_tokens=800
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Executive summary generation failed: {str(e)}"
    
    async def _generate_structured_analysis(self, company_data, research_data: Dict[str, Any], web3_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured analysis components"""
        
        analysis_prompt = f"""
        Based on the research data, provide structured analysis for investment decision:
        
        Company: {company_data.company_name}
        Research: {json.dumps(research_data, indent=2)[:1500]}
        Web3 Analysis: {json.dumps(web3_analysis, indent=2)[:1500]}
        
        Provide JSON response with:
        {{
            "investment_recommendation": "Go/No-Go/Monitor",
            "key_findings": [
                "Finding 1",
                "Finding 2",
                "Finding 3"
            ],
            "risks": [
                "Risk 1",
                "Risk 2",
                "Risk 3"
            ],
            "opportunities": [
                "Opportunity 1",
                "Opportunity 2",
                "Opportunity 3"
            ],
            "next_steps": [
                "Next step 1",
                "Next step 2"
            ]
        }}
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.1,
                max_tokens=1000
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {
                "investment_recommendation": "Monitor",
                "key_findings": [f"Analysis generation failed: {str(e)}"],
                "risks": ["Unable to assess risks due to analysis error"],
                "opportunities": ["Unable to assess opportunities due to analysis error"],
                "next_steps": ["Manual review required"]
            }
    
    async def _generate_pdf_report(self, report_data: Dict[str, Any]) -> str:
        """Generate PDF report"""
        try:
            # Create reports directory if it doesn't exist
            os.makedirs("reports", exist_ok=True)
            
            filename = f"reports/{report_data['company_name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            
            doc = SimpleDocTemplate(filename, pagesize=letter, 
                                  rightMargin=72, leftMargin=72, 
                                  topMargin=72, bottomMargin=18)
            
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=20,
                spaceAfter=30,
            )
            story.append(Paragraph(f"Investment Diligence Report", title_style))
            story.append(Paragraph(f"<b>{report_data['company_name']}</b>", self.styles['Heading2']))
            story.append(Paragraph(f"Generated: {report_data['generated_at']}", self.styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Executive Summary
            story.append(Paragraph("<b>Executive Summary</b>", self.styles['Heading2']))
            story.append(Paragraph(report_data['executive_summary'], self.styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Investment Recommendation
            recommendation = report_data.get('investment_recommendation', 'Monitor')
            rec_style = self.styles['Normal']
            if recommendation == 'Go':
                rec_color = 'green'
            elif recommendation == 'No-Go':
                rec_color = 'red'
            else:
                rec_color = 'orange'
            
            story.append(Paragraph("<b>Investment Recommendation</b>", self.styles['Heading2']))
            story.append(Paragraph(f"<b><font color='{rec_color}'>{recommendation}</font></b>", self.styles['Heading3']))
            story.append(Spacer(1, 20))
            
            # Key Findings
            story.append(Paragraph("<b>Key Findings</b>", self.styles['Heading2']))
            for finding in report_data.get('key_findings', []):
                story.append(Paragraph(f"• {finding}", self.styles['Normal']))
            story.append(Spacer(1, 15))
            
            # Risks
            story.append(Paragraph("<b>Key Risks</b>", self.styles['Heading2']))
            for risk in report_data.get('risks', []):
                story.append(Paragraph(f"• {risk}", self.styles['Normal']))
            story.append(Spacer(1, 15))
            
            # Opportunities
            story.append(Paragraph("<b>Opportunities</b>", self.styles['Heading2']))
            for opp in report_data.get('opportunities', []):
                story.append(Paragraph(f"• {opp}", self.styles['Normal']))
            story.append(Spacer(1, 15))
            
            # Scoring Table (if available)
            scoring = report_data.get('scoring', {})
            if scoring and 'overall_score' in scoring:
                story.append(Paragraph("<b>Framework Scoring</b>", self.styles['Heading2']))
                
                score_data = [
                    ['Metric', 'Score (1-10)'],
                    ['Team Quality', str(scoring.get('team_score', 'N/A'))],
                    ['Technology', str(scoring.get('tech_score', 'N/A'))],
                    ['Market Opportunity', str(scoring.get('market_score', 'N/A'))],
                    ['Overall Score', f"<b>{scoring.get('overall_score', 'N/A')}</b>"]
                ]
                
                table = Table(score_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), '#4472C4'),
                    ('TEXTCOLOR', (0, 0), (-1, 0), '#FFFFFF'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), '#F2F2F2'),
                    ('GRID', (0, 0), (-1, -1), 1, '#000000')
                ]))
                story.append(table)
                story.append(Spacer(1, 15))
            
            # Next Steps
            story.append(Paragraph("<b>Next Steps</b>", self.styles['Heading2']))
            for step in report_data.get('next_steps', []):
                story.append(Paragraph(f"• {step}", self.styles['Normal']))
            
            # Build PDF
            doc.build(story)
            return filename
            
        except Exception as e:
            print(f"PDF generation error: {str(e)}")
            return f"reports/error_{report_data['company_name'].replace(' ', '_')}.txt"