from flask import Flask, render_template, url_for

app = Flask(__name__)

@app.route("/")
def home():
    data = ['LINESTRING(34.79011521585437 32.11589598470496,34.78736863382312 32.06470337558891)', \
            'LINESTRING(34.93019089944812 32.20192792321161,35.13618455179187 32.16705989986249)']
    return render_template('index.html', data = data)

if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True)