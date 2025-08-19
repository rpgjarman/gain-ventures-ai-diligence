import os
import requests
from typing import Dict, Any, Optional
import json

class AirtableClient:
    def __init__(self):
        self.api_key = os.getenv('AIRTABLE_API_KEY')
        self.base_id = os.getenv('AIRTABLE_BASE_ID', 'appxrSHAyyydQq6XY')
        self.table_id = os.getenv('AIRTABLE_TABLE_ID', 'tblyW2riQUpHA2da8')
        self.base_url = f"https://api.airtable.com/v0/{self.base_id}/{self.table_id}"
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    async def get_record_by_external_id(self, external_id: str) -> Optional[Dict[str, Any]]:
        """Find record by external ID"""
        try:
            # Use filter formula to find record
            filter_formula = f"{{External ID}}='{external_id}'"
            url = f"{self.base_url}?filterByFormula={filter_formula}"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            records = data.get('records', [])
            
            if records:
                return records[0]
            return None
            
        except Exception as e:
            print(f"Error fetching record: {str(e)}")
            return None
    
    async def update_record(self, external_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Update record by external ID"""
        try:
            # First find the record
            record = await self.get_record_by_external_id(external_id)
            if not record:
                raise Exception(f"Record not found for external ID: {external_id}")
            
            record_id = record['id']
            
            # Update the record
            url = f"{self.base_url}/{record_id}"
            payload = {
                'fields': fields
            }
            
            response = requests.patch(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Error updating record: {str(e)}")
            raise e
    
    async def create_record(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Create new record"""
        try:
            payload = {
                'fields': fields
            }
            
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Error creating record: {str(e)}")
            raise e
    
    async def get_records_by_status(self, diligence_status: str = "Pending") -> list:
        """Get all records with specific diligence status"""
        try:
            filter_formula = f"{{Diligence Status}}='{diligence_status}'"
            url = f"{self.base_url}?filterByFormula={filter_formula}"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get('records', [])
            
        except Exception as e:
            print(f"Error fetching records: {str(e)}")
            return []