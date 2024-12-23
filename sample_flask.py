from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, World!"  # or render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)