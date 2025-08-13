from flask import Blueprint, request, jsonify, current_app
from ..rate_limit import rate_limit

bp = Blueprint("agents", __name__, url_prefix="/api")

@bp.route("/welcome", methods=["POST"])
@rate_limit()
def welcome_agent_endpoint():
    """HTTP POST: send a message to the WelcomeAgent"""
    data = request.get_json() or {}
    message = data.get("message", "")
    agents = current_app.extensions["agents_registry"]
    agent = agents["welcome"]

    # Example from main.py: classify visitor type
    visitor_type = None
    if 'employer' in message.lower():
        visitor_type = 'employer'
    elif 'client' in message.lower():
        visitor_type = 'client'
    elif 'programmer' in message.lower() or 'developer' in message.lower():
        visitor_type = 'fellow_programmer'

    if 'interest' in message.lower() or 'looking for' in message.lower():
        interest = message.replace('interest', '').replace('looking for', '').strip()
        response = agent.suggest_section(interest)
    else:
        response = agent.greet(visitor_type)

    return jsonify({'response': response})

@bp.route("/project", methods=["POST"])
@rate_limit()
def project_agent_endpoint():
    """Send a message to the ProjectAgent"""
    data = request.get_json() or {}
    message = data.get("message", "")
    agent = current_app.extensions["agents_registry"]["project"]
    response = agent.get_response(message)
    return jsonify({'response': response})

@bp.route("/career", methods=["POST"])
@rate_limit()
def career_agent_endpoint():
    """Send a message to the CareerAgent"""
    data = request.get_json() or {}
    message = data.get("message", "")
    agent = current_app.extensions["agents_registry"]["career"]
    response = agent.get_response(message)
    return jsonify({'response': response})

@bp.route("/client", methods=["POST"])
@rate_limit()
def client_agent_endpoint():
    """Send a message to the ClientAgent"""
    data = request.get_json() or {}
    message = data.get("message", "")
    agent = current_app.extensions["agents_registry"]["client"]
    response = agent.get_response(message)
    return jsonify({'response': response})

@bp.route("/research", methods=["POST"])
@rate_limit()
def research_agent_endpoint():
    """Send a message to the ResearchAgent"""
    data = request.get_json() or {}
    message = data.get("message", "")
    agent = current_app.extensions["agents_registry"]["research"]
    response = agent.get_response(message)
    return jsonify({'response': response})