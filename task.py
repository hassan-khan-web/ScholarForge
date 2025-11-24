import os
from dotenv import load_dotenv
load_dotenv()
from celery import Celery
import AI_engine 

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

celery_app = Celery('task', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

# In task.py

@celery_app.task(bind=True)
def generate_report_task(self, query: str, user_format: str, page_count: int) -> dict:
    try:
        # 1. Run the Engine
        result = AI_engine.run_ai_engine_with_return(query, user_format, page_count, task=self)
        
        if isinstance(result, str):
            self.update_state(state='FAILURE', meta={'message': result})
            return {'status': 'FAILURE', 'error': result}
        
        search_content, report_content = result
        
        # 2. Force an update right before returning to ensure frontend sees it
        self.update_state(state='PROGRESS', meta={'message': 'Step 5/5: Finalizing document...'})
        
        # 3. Return the result
        return {
            'status': 'SUCCESS',
            'search_content': search_content,
            'report_content': report_content
        }

    except Exception as e:
        self.update_state(state='FAILURE', meta={'message': f"Critical Error: {str(e)}"})
        return {'status': 'FAILURE', 'error': str(e)}