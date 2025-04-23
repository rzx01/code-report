from flask import Blueprint
from ..controllers.file_controller import gen_pdf

file_bp = Blueprint("file", __name__)

# Route to generate a report
file_bp.add_url_rule("/gen_pdf", view_func=gen_pdf, methods=["POST"])
