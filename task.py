import os
from celery import Celery
import AI_engine  # This imports your engine

# Configure Celery
# We use Redis as the message broker
celery_app = Celery(
    'scholarforge_tasks',
    broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

@celery_app.task(bind=True)
def generate_report_task(self, query: str, format_content: str, page_count: int):
    """
    Background task to run the AI Engine.
    Takes 'page_count' to support the new tiered logic.
    """
    try:
        self.update_state(state='PROGRESS', meta={'message': 'Initializing AI Engine...'})
        
        # Call the engine
        # We pass 'self' (the task instance) so the engine can update the progress status
        search_content, report_content = AI_engine.run_ai_engine_with_return(
            query, 
            format_content, 
            page_count,
            task=self
        )

        return {
            'status': 'SUCCESS',
            'search_content': search_content,
            'report_content': report_content
        }
    except Exception as e:
        return {'status': 'FAILURE', 'error': str(e)}