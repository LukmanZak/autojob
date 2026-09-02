from pydantic import BaseModel, Field
from typing import Optional
import datetime

class JobPosting(BaseModel):
    source: str  # disnakerja|jobstreet|glints
    keyword: str
    posted_date: str  # YYYY-MM-DD
    scraped_at: str
    title: str
    company: str = ""
    location: str = ""
    country: str = ""
    salary: str = ""
    url: str
    job_id: str = ""
    description_snippet: str = ""
    
    def to_csv_row(self):
        return self.model_dump()
