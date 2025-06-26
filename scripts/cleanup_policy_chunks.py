import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from app import create_app
from app.models import Policy, PolicyChunk
from app.db import db

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_policy_chunks():
    app = create_app()
    with app.app_context():
        policies = Policy.query.all()
        total_deleted = 0
        for policy in policies:
            expected_filename = policy.document_source_filename
            # Find chunks for this policy_id that do NOT match the expected filename
            bad_chunks = PolicyChunk.query.filter(
                PolicyChunk.policy_id == policy.id,
                PolicyChunk.document_source_filename != expected_filename
            ).all()
            if bad_chunks:
                logger.info(f"Policy ID {policy.id}: Removing {len(bad_chunks)} bad chunks (should match: {expected_filename})")
                for chunk in bad_chunks:
                    db.session.delete(chunk)
                total_deleted += len(bad_chunks)
        db.session.commit()
        logger.info(f"Cleanup complete. Total bad chunks deleted: {total_deleted}")

if __name__ == "__main__":
    cleanup_policy_chunks() 