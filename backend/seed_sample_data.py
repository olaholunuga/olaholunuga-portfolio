# backend/seed_sample_data.py
"""
Insert a few sample Projects and Skills so the frontend has data to show.
Run after create_db: python seed_sample_data.py
"""

from app import create_app
from app.models import Project, Skill
from app.db import get_db
from app.config import Config

def seed():
    app = create_app(Config)
    with app.app_context():
        # Create some sample records if none exist
        with get_db() as db:
            if db.query(Project).count() == 0:
                p1 = Project(title="AI Agent Portfolio", summary="Agent-powered portfolio UI", description="Based on ai-agent-app", github_url="https://github.com/olaholunuga/ai-portfolio")
                p2 = Project(title="Static Site Generator", summary="Personal blog SSG", description="Markdown-based SSG", github_url="https://github.com/olaholunuga/ssg")
                db.add_all([p1, p2])
                print("Inserted sample projects.")
            if db.query(Skill).count() == 0:
                s1 = Skill(name="Python", level="Advanced", category="Backend")
                s2 = Skill(name="React", level="Intermediate", category="Frontend")
                db.add_all([s1, s2])
                print("Inserted sample skills.")

if __name__ == "__main__":
    seed()
