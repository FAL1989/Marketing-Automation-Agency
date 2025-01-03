from locust import HttpUser, task, between

class AIAgencyUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        self.token = 'test_token'
    
    @task(3)
    def query_ai(self):
        headers = {'Authorization': f'Bearer {self.token}'}
        prompt = 'Como otimizar performance?'
        
        with self.client.post(
            '/api/v1/ai/query',
            json={'prompt': prompt},
            headers=headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f'Falha na consulta: {response.status_code}')
    
    @task(1)
    def health_check(self):
        self.client.get('/api/v1/health')