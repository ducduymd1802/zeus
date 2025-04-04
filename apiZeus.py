import requests
import json
from flask import Flask, jsonify, request, render_template
import os
from apscheduler.schedulers.background import BackgroundScheduler
import time
import logging

app = Flask(__name__)
# Định cấu hình logging
logging.basicConfig(level=logging.INFO)

# Lưu trữ dữ liệu instock gần đây nhất
latest_instock_data = {}
last_update_time = None

# API key mặc định (bạn nên lưu trữ trong biến môi trường thay vì hardcode)
DEFAULT_API_KEY = os.environ.get('API_KEY', '7425079c-9b59-4529-8cd4-e1029a8d808d')
API_BASE_URL = "https://api.zeus-x.ru/stock/instock"

def get_account_instock(account_code=None):
    """Lấy dữ liệu instock từ API gốc
    
    Args:
        account_code (str, optional): Mã tài khoản cụ thể cần lấy. Nếu None, lấy tất cả.
    """
    try:
        # Xây dựng URL dựa trên tham số
        if account_code:
            api_url = f"{API_BASE_URL}/{account_code}?key={DEFAULT_API_KEY}"
        else:
            api_url = f"{API_BASE_URL}?key={DEFAULT_API_KEY}"
        
        logging.info(f"Đang gửi request đến: {api_url}")
        response = requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()
            
            if "Code" in data and "Data" in data and data["Code"] == 0:
                instock_data = {}
                
                for item in data["Data"]:
                    item_account_code = item.get("AccountCode")
                    instock = item.get("Instock")
                    name = item.get("Name")
                    price = item.get("Price")
                    desc = item.get("Desc")
                    live = item.get("Live")
                    img_url = item.get("Img")
                    
                    if item_account_code and instock is not None:
                        instock_data[item_account_code] = {
                            "instock": instock,
                            "name": name,
                            "price": price,
                            "description": desc,
                            "live_duration": live,
                            "image_url": img_url,
                            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                
                return instock_data
            else:
                logging.error(f"Định dạng response không đúng: {data}")
                return None
        else:
            logging.error(f"Request thất bại với mã trạng thái: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Đã xảy ra lỗi: {str(e)}")
        return None

def update_instock_data():
    """Cập nhật dữ liệu instock định kỳ"""
    global latest_instock_data, last_update_time
    
    logging.info("Đang cập nhật dữ liệu instock...")
    data = get_account_instock()
    
    if data:
        latest_instock_data = data
        last_update_time = time.strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"Cập nhật dữ liệu thành công. Đã tìm thấy {len(data)} loại tài khoản.")
    else:
        logging.error("Không thể cập nhật dữ liệu")

# Trang chủ - hiển thị dữ liệu dưới dạng HTML
@app.route('/')
def home():
    return render_template('index.html', 
                          data=latest_instock_data, 
                          last_update=last_update_time)

# API endpoint để lấy tất cả dữ liệu instock
@app.route('/api/instock', methods=['GET'])
def get_all_instock():
    # Kiểm tra nếu cần refresh dữ liệu
    refresh = request.args.get('refresh', 'false').lower() == 'true'
    if refresh:
        update_instock_data()
    
    return jsonify({
        "success": True,
        "data": latest_instock_data,
        "last_update": last_update_time,
        "count": len(latest_instock_data)
    })

# API endpoint để lấy dữ liệu instock cho một loại tài khoản cụ thể
@app.route('/api/instock/<account_code>', methods=['GET'])
def get_specific_instock(account_code):
    # Kiểm tra nếu cần refresh dữ liệu
    refresh = request.args.get('refresh', 'false').lower() == 'true'
    if refresh:
        # Chỉ cập nhật dữ liệu cho loại tài khoản cụ thể
        account_data = get_account_instock(account_code)
        if account_data and account_code in account_data:
            latest_instock_data[account_code] = account_data[account_code]
    
    if account_code in latest_instock_data:
        return jsonify({
            "success": True,
            "account_code": account_code,
            "data": latest_instock_data[account_code]
        })
    else:
        return jsonify({
            "success": False,
            "error": "Account code not found"
        }), 404
        
# Endpoint để buộc cập nhật dữ liệu
@app.route('/api/refresh', methods=['GET'])
def force_refresh():
    update_instock_data()
    return jsonify({
        "success": True,
        "message": "Dữ liệu đã được cập nhật",
        "last_update": last_update_time
    })

# Khởi tạo lịch cập nhật dữ liệu
scheduler = BackgroundScheduler()
scheduler.add_job(func=update_instock_data, trigger="interval", minutes=10)
scheduler.start()

# Chạy cập nhật dữ liệu lần đầu khi khởi động
update_instock_data()

if __name__ == '__main__':
    # Tạo thư mục templates nếu chưa tồn tại
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Tạo file HTML template cơ bản
    with open('templates/index.html', 'w') as f:
        f.write('''
<!DOCTYPE html>
<html>
<head>
    <title>Instock Checker</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
        .refresh-btn { padding: 10px 15px; background-color: #4CAF50; color: white; border: none; 
                      border-radius: 4px; cursor: pointer; }
        .last-update { margin: 10px 0; color: #666; }
    </style>
</head>
<body>
    <h1>Instock Checker</h1>
    <p class="last-update">Cập nhật lần cuối: {{ last_update or 'Chưa có dữ liệu' }}</p>
    <button class="refresh-btn" onclick="location.reload()">Làm mới dữ liệu</button>
    
    <table>
        <thead>
            <tr>
                <th>Account Code</th>
                <th>Name</th>
                <th>Price</th>
                <th>Instock</th>
                <th>Description</th>
                <th>Live Duration</th>
            </tr>
        </thead>
        <tbody>
            {% if data %}
                {% for account_code, info in data.items() %}
                <tr>
                    <td>{{ account_code }}</td>
                    <td>{{ info.name }}</td>
                    <td>{{ info.price }}</td>
                    <td>{{ info.instock }}</td>
                    <td>{{ info.description }}</td>
                    <td>{{ info.live_duration }}</td>
                </tr>
                {% endfor %}
            {% else %}
                <tr>
                    <td colspan="4">Không có dữ liệu</td>
                </tr>
            {% endif %}
        </tbody>
    </table>
    
    <div style="margin-top: 30px;">
        <h2>API Usage</h2>
        <p>Get all instock data: <code>/api/instock</code></p>
        <p>Get specific account data: <code>/api/instock/{account_code}</code></p>
    </div>
</body>
</html>
        ''')
    
    # Chạy ứng dụng Flask
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)