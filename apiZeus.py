from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# Mapping từ key sang AccountCode
def get_account_code_by_key(key):
    key_to_account_code = {
        '7425079c-9b59-4529-8cd4-e1029a8d808d': 'HOTMAIL',
        '4ca32193-4bd9-47a9-8ee6-b4c058bc9857': 'HOTMAIL_TRUSTED',
    }
    return key_to_account_code.get(key)

# Lấy dữ liệu Instock từ API bên ngoài
def get_instock_by_account_code(account_code):
    try:
        response = requests.get('https://api.zeus-x.ru/stock/instock', timeout=5)
        response.raise_for_status()  
        data = response.json()

        if data.get('Code') != 0 or not isinstance(data.get('Data'), list):
            return None  

        for item in data['Data']:
            if item.get('AccountCode') == account_code:
                return item.get('Instock')

        return None  

    except requests.exceptions.RequestException:
        return None  

# Sửa route thành "/"
@app.route('/', methods=['GET'])
def get_instock():
    key = request.args.get('key')  # Lấy key từ URL query params
    
    if not key:
        return jsonify({"error": "Missing key parameter"}), 400
    
    account_code = get_account_code_by_key(key)
    
    if not account_code:
        return jsonify({"error": "Invalid key"}), 403

    instock = get_instock_by_account_code(account_code)

    if instock is None:
        return jsonify({"error": "Data not found"}), 404

    return jsonify({"sum": instock})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
