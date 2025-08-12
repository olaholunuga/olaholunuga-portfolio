"""
Proxy endpoint to fetch latest posts from blog API.
"""
import requests
from flask import Blueprint, jsonify, current_app
from ..rate_limit import rate_limit

bp = Blueprint("blog_proxy", __name__, url_prefix="/api/blog")

@bp.route("/latest", methods=["GET"])
@rate_limit()
def get_latest_posts():
    blog_api_url = f"{current_app.config['BLOG_API_URL']}/posts?limit=3"
    try:
        resp = requests.get(blog_api_url, timeout=5)
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.RequestException as e:
        return jsonify({"error": "Failed to fetch blog posts", "details": str(e)}), 500
