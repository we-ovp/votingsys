from flask import Flask, render_template, request, redirect, session, send_file
import os
import csv
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = "schoolvotingsystem"  # Secret key for session

# Create record.csv if it doesn't exist
if not os.path.exists('record.csv'):
    with open('record.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['timestamp', 'name', 'phone', 'house', 'position1_vote', 'position2_vote', 'position3_vote'])

# Create voters.json if it doesn't exist
if not os.path.exists('voters.json'):
    with open('voters.json', 'w') as file:
        json.dump([], file)

@app.route('/')
def index():
    if 'logged_in' in session:
        session.clear()  # Clear any existing session
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    name = request.form.get('name')
    phone = request.form.get('phone')
    house = request.form.get('house')
    
    # Check if admin login
    if name == 'admin' and phone == '1234567890':
        session['is_admin'] = True
        return redirect('/admin')
    
    # Check if user has already voted
    with open('voters.json', 'r') as file:
        voters = json.load(file)
        
    for voter in voters:
        if voter['phone'] == phone:
            return render_template('index.html', error="You have already voted.")
    
    # Add user to session
    session['logged_in'] = True
    session['name'] = name
    session['phone'] = phone
    session['house'] = house
    session['votes'] = {}
    
    return redirect('/voting1')

@app.route('/voting1')
def voting1():
    if 'logged_in' not in session:
        return redirect('/')
    return render_template('voting1.html')

@app.route('/submit_vote1', methods=['POST'])
def submit_vote1():
    if 'logged_in' not in session:
        return redirect('/')
    
    selected_candidate = request.form.get('candidate')
    session['votes']['position1'] = selected_candidate
    
    return redirect('/voting2')

@app.route('/voting2')
def voting2():
    if 'logged_in' not in session:
        return redirect('/')
    return render_template('voting2.html')

@app.route('/submit_vote2', methods=['POST'])
def submit_vote2():
    if 'logged_in' not in session:
        return redirect('/')
    
    selected_candidate = request.form.get('candidate')
    session['votes']['position2'] = selected_candidate
    
    return redirect('/voting3')

@app.route('/voting3')
def voting3():
    if 'logged_in' not in session:
        return redirect('/')
    return render_template('voting3.html')

@app.route('/submit_vote3', methods=['POST'])
def submit_vote3():
    if 'logged_in' not in session:
        return redirect('/')
    
    selected_candidate = request.form.get('candidate')
    session['votes']['position3'] = selected_candidate
    
    # Record vote in CSV
    with open('record.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            session['name'],
            session['phone'],
            session['house'],
            session['votes'].get('position1', ''),
            session['votes'].get('position2', ''),
            session['votes'].get('position3', '')
        ])
    
    # Record voter to prevent re-voting
    with open('voters.json', 'r') as file:
        voters = json.load(file)
    
    voters.append({
        'name': session['name'],
        'phone': session['phone'],
        'house': session['house']
    })
    
    with open('voters.json', 'w') as file:
        json.dump(voters, file)
    
    return redirect('/thanks')

@app.route('/thanks')
def thanks():
    if 'logged_in' not in session:
        return redirect('/')
    
    # Clear session after displaying thanks
    name = session.get('name', '')
    session.clear()
    
    return render_template('thanks.html', name=name)

@app.route('/admin')
def admin():
    if 'is_admin' not in session:
        return redirect('/')
    
    # Read record.csv for displaying results
    votes_data = []
    try:
        with open('record.csv', 'r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                votes_data.append(row)
    except:
        pass
    
    # Calculate statistics
    total_votes = len(votes_data)
    house_counts = {}
    position1_counts = {}
    position2_counts = {}
    position3_counts = {}
    
    for vote in votes_data:
        # Count by house
        house = vote.get('house', 'Unknown')
        house_counts[house] = house_counts.get(house, 0) + 1
        
        # Count by position votes
        pos1 = vote.get('position1_vote', 'None')
        position1_counts[pos1] = position1_counts.get(pos1, 0) + 1
        
        pos2 = vote.get('position2_vote', 'None')
        position2_counts[pos2] = position2_counts.get(pos2, 0) + 1
        
        pos3 = vote.get('position3_vote', 'None')
        position3_counts[pos3] = position3_counts.get(pos3, 0) + 1
    
    return render_template('admin.html', 
                          votes_data=votes_data, 
                          total_votes=total_votes,
                          house_counts=house_counts,
                          position1_counts=position1_counts,
                          position2_counts=position2_counts,
                          position3_counts=position3_counts)

@app.route('/download_csv')
def download_csv():
    if 'is_admin' not in session:
        return redirect('/')
    
    return send_file('record.csv',
                     mimetype='text/csv',
                     download_name='voting_records.csv',
                     as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)