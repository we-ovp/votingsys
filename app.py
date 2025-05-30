from flask import Flask, render_template, request, redirect, session
import os
import json

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Load candidates
with open('candidates.json') as f:
    CANDIDATES = json.load(f)

# Create results.json if not exists
if not os.path.exists('results.json'):
    results = {}
    for group in CANDIDATES.values():
        for role, candidates in group.items():
            if role not in results:
                results[role] = {}
            for candidate in candidates:
                if isinstance(candidate, dict) and "name" in candidate:
                    results[role][candidate["name"]] = 0
                elif isinstance(candidate, str):
                    results[role][candidate] = 0
    with open('results.json', 'w') as f:
        json.dump(results, f, indent=4)

# Load voters
with open('voters.json') as f:
    VOTERS = json.load(f)

@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = next((v for v in VOTERS if v['username'] == username and v['password'] == password), None)

    if user:
        if user.get('voted') and username != 'admin':
            return render_template('index.html', error='You have already voted.')
        session['user'] = user
        if username == 'admin':
            return redirect('/admin')
        return redirect('/voting_common')
    return render_template('index.html', error='Invalid credentials.')

@app.route('/voting_common', methods=['GET', 'POST'])
def voting_common():
    if 'user' not in session:
        return redirect('/')
    if request.method == 'POST':
        session['votes'] = request.form.to_dict()
        return redirect('/voting_house')
    return render_template('voting_common.html', candidates=CANDIDATES["common"])

@app.route('/voting_house', methods=['GET', 'POST'])
def voting_house():
    if 'user' not in session:
        return redirect('/')
    house = session['user'].get('house')
    if house not in CANDIDATES:
        return redirect('/thanks')  # Skip if house is invalid or not found
    if request.method == 'POST':
        session['votes'].update(request.form.to_dict())
        with open('results.json') as f:
            results = json.load(f)

        for role, candidate in session['votes'].items():
            if role not in results:
                results[role] = {}
            if candidate not in results[role]:
                results[role][candidate] = 0
            results[role][candidate] += 1

        with open('results.json', 'w') as f:
            json.dump(results, f, indent=4)

        for v in VOTERS:
            if v['username'] == session['user']['username']:
                v['voted'] = True
        with open('voters.json', 'w') as f:
            json.dump(VOTERS, f, indent=4)

        return redirect('/thanks')
    return render_template('voting_house.html', candidates=CANDIDATES.get(house, {}))

@app.route('/thanks')
def thanks():
    name = session.get('user', {}).get('username', 'Voter')
    session.clear()
    return render_template('thanks.html', name=name)

@app.route('/admin')
def admin():
    if session.get('user', {}).get('username') != 'admin':
        return redirect('/')
    with open('results.json') as f:
        results = json.load(f)
    return render_template('admin.html', results=results)

if __name__ == "__main__":
    app.run(debug=True)

