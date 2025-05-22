from flask import Flask, request, jsonify
import os
import json
from datetime import datetime

app = Flask(__name__)

# JSON file path in user's home directory
user_home = os.path.expanduser('~')
flashcards_file = os.path.join(user_home, 'AllFlashcards.json')

# Ensure JSON file exists and contains a list
def initialize_json_file():
    if not os.path.exists(flashcards_file):
        with open(flashcards_file, 'w') as f:
            json.dump([], f)
    else:
        try:
            with open(flashcards_file, 'r') as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("JSON is not a list")
        except Exception:
            # If file is corrupted or invalid, reset it
            with open(flashcards_file, 'w') as f:
                json.dump([], f)
@app.route('/submit', methods=['GET'])
def submit_data():
    initialize_json_file()

    searchStore = request.args.get('searchStore')  # was InsertItems
    insertStore = request.args.get('insertStore')
    storename = request.args.get('storename', '').strip()
    storeIP = request.args.get('storeIP', '').strip()
    storeCo = request.args.get('storeCo', '').strip()
    itemname = request.args.get('itemname', '').strip()
    password = request.args.get('password', '')

    # Password check
    if password != 'abcd':
        return jsonify({'error': 'Unauthorized'}), 403

    # Validate insertStore and searchStore
    if searchStore not in ['0', '1'] or insertStore not in ['0', '1']:
        return jsonify({'error': 'searchStore and insertStore must be 0 or 1'}), 400

    if not storename:
        return jsonify({'error': 'storename is required'}), 400

    searchStore = int(searchStore)
    insertStore = int(insertStore)

    try:
        with open(flashcards_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        return jsonify({'error': f'Failed to load JSON file: {str(e)}'}), 500

    existing_store = next((store for store in data if store['storename'].lower() == storename.lower()), None)

    if insertStore == 0:
        # Just return store JSON if found, else 404
        if existing_store:
            return jsonify(existing_store), 200
        else:
            return jsonify({'error': f'Store "{storename}" not found'}), 404

    # insertStore == 1: insert or update store
    if not itemname:
        return jsonify({'error': 'itemname is required when inserting/updating'}), 400

    if existing_store:
        if 'itemslist' not in existing_store or not isinstance(existing_store['itemslist'], list):
            existing_store['itemslist'] = []

        existing_store['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if itemname not in existing_store['itemslist']:
            existing_store['itemslist'].append(itemname)
        existing_store['storeIP'] = storeIP
        existing_store['storeCo'] = storeCo

        message = 'Store updated'
    else:
        new_store = {
            'storename': storename,
            'storeIP': storeIP,
            'storeCo': storeCo,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'itemslist': [itemname]
        }
        data.append(new_store)
        message = 'New store added'

    try:
        with open(flashcards_file, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        return jsonify({'error': f'Failed to save data: {str(e)}'}), 500

    return jsonify({
        'message': message,
        'storename': storename,
        'path': flashcards_file
    }), 200
