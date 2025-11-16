from flask import Flask, render_template, jsonify, request
import pandas as pd
import altair as alt
import json
from pathlib import Path
from load_data import PolitigraphAPI,prep_data,get_data
from flask_cors import CORS

app = Flask(__name__)
# CORS(app)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
# ============================================
# FUNCTION: อ่านข้อมูลจาก CSV
# ============================================


@app.route('/api/get_history', methods=['POST'])
def get_history():
    data = request.get_json()
    mp_id = data.get('mpId')
    
    df = get_data(id=None)
    
    # Filter by voter_id if provided
    if mp_id:
        df = df[df['voter_id'].astype(str) == str(mp_id)]
    
    result = df[['start_date','title','id','voter_id','voter_name','vote_option','voter_party']].fillna('').to_dict(orient='records')
    return jsonify(result), 200

@app.route('/api/get_df', methods=['POST'])
def get_df():
    """Execute a GraphQL query sent in the POST body as JSON { "query": "..."}"""
    payload = request.get_json(silent=True) or {}
    sessionId = payload.get("sessionId")
    """Execute a GraphQL query sent in the POST body as JSON { "query": "..."}"""
    df = get_data(sessionId)
    result = df[['voter_name','vote_category','voter_id','voter_party']].fillna('').to_dict(orient='records')
    return jsonify(result), 200

@app.route('/api/get_session', methods=['GET'])  # ✅ เปลี่ยนเป็น GET
def get_session():
    """Get all voting sessions"""
    df = get_data(id=None)
    df = df[df['nickname']!='มติเลือกนายกรัฐมนตรีคนที่ 32']
    df = df[['id','nickname','description','result','end_date']] \
        .rename(columns={
            'end_date': 'date',
            'nickname': 'billName'  # ✅ แก้จาก 'title' เป็น 'nickname'
        }) \
        .drop_duplicates().dropna(subset=['billName']).fillna('')
    result = df.to_dict(orient='records')  # ✅ แก้ typo: orient
    return jsonify(result), 200

@app.route('/api/get_parties', methods=['POST'])
def get_parties():
    payload = request.get_json(silent=True) or {}
    sessionId = payload.get("sessionId")
    """Execute a GraphQL query sent in the POST body as JSON { "query": "..."}"""
    df = get_data(sessionId)
    df = df.groupby(['nickname','voter_party','vote_category']).agg(count=('voter_party','count')).reset_index()

    # ทำ pivot เพื่อแยก agree / disagree / Abstain ออกเป็นคอลัมน์
    pivot_df = df.pivot_table(
        index=['voter_party','nickname'],
        columns='vote_category',
        values='count',
        aggfunc='sum',
        fill_value=0
    ).reset_index().fillna('')

    # เปลี่ยนชื่อคอลัมน์ให้เป็นอังกฤษและ lowercase
    pivot_df = pivot_df.rename(columns={
        'voter_party': 'party',
        'agree': 'agree',
        'disagree': 'disagree',
        'Abstain': 'abstain'
    })
    # แปลงเป็น list ของ dict
    json_list = pivot_df.to_dict(orient='records')
    # แปลงเป็น JSON string พร้อมใช้งาน
    # json_str = json.dumps(json_list, ensure_ascii=False, indent=2)
    return jsonify(json_list), 200

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 เริ่มต้น Flask Application")
    print("=" * 60)
    port= 5000
    print("\n" + "=" * 60)
    print("✨ เปิดเว็บไซต์ที่: http://127.0.0.1:5000")
    print("=" * 60 + "\n")
    # Production mode
    app.run(host='0.0.0.0', port=port, debug=False)
