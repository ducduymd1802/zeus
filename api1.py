from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

# Hàm kiểm tra usercode
def check(usercode):
    if usercode == "257966565":
        return {"status": "success", "message": "Valid user", "data": {"key": "value"}}
    else:
        return {"status": "error", "message": "Invalid user"}

# Lấy dữ liệu Instock từ API bên ngoài
def get_instock_by_account_code(account_code):
    try:
        response = requests.get('https://api.zeus-x.ru/stock/instock', timeout=5)  # Thêm timeout để tránh treo
        response.raise_for_status()  # Tự động raise lỗi nếu HTTP status code không phải 200
        data = response.json()

        # Kiểm tra cấu trúc JSON
        if data.get('Code') != 0 or not isinstance(data.get('Data'), list):
            return {"error": "Unexpected API response format"}

        # Tìm AccountCode phù hợp
        for item in data['Data']:
            if item.get('AccountCode') == account_code:
                return {"instock": item.get('Instock')}

        return {"error": "AccountCode not found"}

    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}

# Mapping từ key sang AccountCode
def get_account_code_by_key(key):
    key_to_account_code = {
        '7425079c-9b59-4529-8cd4-e1029a8d808d': 'HOTMAIL',
        '4ca32193-4bd9-47a9-8ee6-b4c058bc9857': 'HOTMAIL_TRUSTED',
    }
    return key_to_account_code.get(key)

# Lấy Instock bằng key
def get_instock_by_key(key):
    account_code = get_account_code_by_key(key)
    if not account_code:
        return {"error": "Invalid key"}

    return get_instock_by_account_code(account_code)

# Endpoint kiểm tra usercode
@app.route('/<usercode>', methods=['GET'])
def check_usercode(usercode):
    return jsonify(check(usercode))

# Endpoint lấy instock theo key
@app.route('/input', methods=['GET'])
def get_instock():
    key = request.args.get('key')
    if not key:
        return jsonify({"error": "Missing key parameter"}), 400

    return jsonify(get_instock_by_key(key))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
