from flask import Flask, jsonify

app = Flask(__name__)

def check(usercode):
    if usercode == "257966565":
        return {"status": "success", "message": "Valid user", "data": {"key": "value"}}
    else:
        return {"status": "error", "message": "Invalid user"}

@app.route('/<usercode>', methods=['GET'])
def api(usercode):
    return jsonify(check(usercode))

if __name__ == '__main__':
    app.run(debug=True)
