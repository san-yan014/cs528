import functions_framework
from googleapiclient import discovery
from google.auth import default

PROJECT_ID = 'direct-electron-486319-t6'
INSTANCE_NAME = 'hw5-db'

@functions_framework.http
def stop_database(request):
    try:
        credentials, _ = default()
        service = discovery.build('sqladmin', 'v1', credentials=credentials)
        
        instance = service.instances().get(
            project=PROJECT_ID,
            instance=INSTANCE_NAME
        ).execute()
        
        current_state = instance.get('state')
        
        if current_state == 'RUNNABLE':
            print(f'database {INSTANCE_NAME} is running, stopping it...')
            service.instances().patch(
                project=PROJECT_ID,
                instance=INSTANCE_NAME,
                body={'settings': {'activationPolicy': 'NEVER'}}
            ).execute()
            return f'stopped database {INSTANCE_NAME}', 200
        else:
            print(f'database {INSTANCE_NAME} already stopped (state: {current_state})')
            return f'database already stopped', 200
            
    except Exception as e:
        print(f'error: {e}')
        return f'error stopping database: {e}', 500