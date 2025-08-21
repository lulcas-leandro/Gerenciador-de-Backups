from flask import Blueprint, render_template

routes_bp = Blueprint('principal', __name__)

@routes_bp.route('/')
def painel():
    return render_template('index.html')
