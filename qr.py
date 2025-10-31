from flask import Flask, request, jsonify
import pandas as pd

df = pd.read_csv("/Users/jigyasaverma/Desktop/backend/Edu_cred_verify/EduCred-Verify/datasets/ocr_dataset.csv")

app = Flask(__name__)

@app.route("/verify", methods=["GET"])
def verify_certificate():
    cert_id = request.args.get("cert_id")

    if not cert_id:
        return jsonify({"error": "cert_id is required"}), 400
    record = df[df["cert_id"] == cert_id]

    if not record.empty:
        return jsonify({"status": "valid", "data": record.to_dict(orient="records")[0]})
    else:
        return jsonify({"status": "invalid", "message": "Certificate not found"})

if __name__ == "__main__":
    app.run(debug=True)
