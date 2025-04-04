from flask import Flask, jsonify, request
import requests
import json

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

# Function xử lý mua hàng
def buy_order(account_code, quantity):
    try:
        # Gọi API mua hàng
        api_url = f'https://api.zeus-x.ru/purchase?apikey=219d902a3ef44930836e3ba86cc462e9&accountcode={account_code}&quantity={quantity}'
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Kiểm tra xem API có trả về thành công không
        if data.get('Code') != 0 or data.get('Message') != "YOU HAVE SUCCESSFULLY PURCHASED":
            return jsonify({"error": "Purchase failed", "details": data}), 400

        # Trích xuất danh sách các tài khoản mail
        accounts = data.get('Data', {}).get('Accounts', [])
        
        # Chuyển đổi sang định dạng mong muốn: [{"product":"Email|Password|RefreshToken|ClientId"}, ...]
        formatted_accounts = []
        for account in accounts:
            # Tạo chuỗi theo định dạng "Mail|Pass|RefreshToken|ClientId"
            formatted_mail = f"{account.get('Email')}|{account.get('Password')}|{account.get('RefreshToken')}|{account.get('ClientId')}"
            formatted_accounts.append({"product": formatted_mail})
            
        return jsonify(formatted_accounts)

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Network error", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Unexpected error", "details": str(e)}), 500

# Route chính "/"
@app.route('/', methods=['GET'])
def api_endpoint():
    key = request.args.get('key')  # Lấy key từ URL query params
    
    if not key:
        return jsonify({"error": "Missing key parameter"}), 400
    
    account_code = get_account_code_by_key(key)
    
    if not account_code:
        return jsonify({"error": "Invalid key"}), 403

    # Kiểm tra xem có tham số quantity không
    quantity = request.args.get('quantity')
    
    # Nếu có quantity, xử lý mua hàng
    if quantity is not None:
        # Trường hợp đặc biệt: nếu quantity={quantity} thì đây là API test, quantity=2
        if quantity == "{quantity}":
            quantity = 2
            return buy_order(account_code, quantity)
        
        try:
            quantity = int(quantity)
            return buy_order(account_code, quantity)
        except ValueError:
            return jsonify({"error": "Quantity must be a number"}), 400
    
    # Nếu không, trả về sum (instock) như trước
    instock = get_instock_by_account_code(account_code)

    if instock is None:
        return jsonify({"error": "Data not found"}), 404

    return jsonify({"sum": instock})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)