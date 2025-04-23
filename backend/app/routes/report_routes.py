from flask import Blueprint
from ..controllers.report_controller import get_commits, generate_report, summary

report_bp = Blueprint("report", __name__)

# Route to fetch commits based on duration and username
report_bp.add_url_rule("/commit", view_func=get_commits)

# Route to generate a report
report_bp.add_url_rule("/generate", view_func=generate_report, methods=["POST"])