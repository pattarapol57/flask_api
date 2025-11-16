import requests
import json
import pandas as pd
from typing import Dict, Any, Optional

class PolitigraphAPI:
    """
    คลาสสำหรับดึงข้อมูลจาก Politigraph GraphQL API
    """
    
    def __init__(self):
        self.url = "https://politigraph.wevis.info/graphql"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def query(self, query_string: str, variables: Optional[Dict[str, Any]] = None) -> Dict:
        """
        ส่ง GraphQL query ไปยัง API
        
        Parameters:
        -----------
        query_string : str
            GraphQL query string
        variables : dict, optional
            ตัวแปรสำหรับ query
        
        Returns:
        --------
        dict : ข้อมูลที่ได้จาก API
        """
        payload = {
            "query": query_string.strip()
        }
        
        if variables:
            payload["variables"] = variables
        
        try:
            response = requests.post(
                self.url,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "errors" in data:
                print(f"❌ GraphQL Errors: {data['errors']}")
                return None
            
            return data.get("data")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            return None


def get_data(id='a6817071-768c-462a-bc50-39eb57dd4cf9'):
    df = pd.read_csv('df_votes.csv')
    df = prep_data(df)
    if id is not None:
        df = df[df['id']==id]
    return df

def map_name(df):
    df_map = pd.read_csv('party_name.csv')
    mapping = dict(zip(df_map['voter_party'].str.strip(), df_map['New_party_name'].str.strip()))
    df['voter_party'] = df['voter_party'].str.strip().map(mapping).fillna('')
    return df 

def filter_data(df):
    df = df[~(df['voter_party'].isin(['-','','สมาชิกวุฒิสภา']))].reset_index(drop=True)
    return df 

def prep_data(df):
    df = map_name(df)
    df = filter_data(df)
    vote_mapping = {
        'เห็นด้วย': 'agree',
        'ไม่เห็นด้วย': 'disagree',
        'ลา / ขาดลงมติ': 'absent',
        'ไม่ลงคะแนนเสียง': 'no-vote',
        'งดออกเสียง': 'abstain'
    }
    # df = df[pd.notna(df['nickname'])]
    result_mapping = {'ผ่าน':'passed','ไม่ผ่าน':'failed'}
    df['description'] = df['description'].fillna('')
    df['result'] = df['result'].map(result_mapping).fillna('failed')
    df['vote_category'] = df['vote_option'].map(vote_mapping).fillna('absent')
    return df 