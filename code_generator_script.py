from locust import HttpUser, task, between
import time
import pandas as pd
from models import SessionLocal, generate_sequential_code, engine, User
from bs4 import BeautifulSoup




class WebhookUser(HttpUser):
    """
    Simulates a user sending data to the database via a webhook.
    """
    wait_time = between(1, 2.5)  # Simulate user wait time between tasks
    tasks_executed = False  # Track if tasks have been executed

    def get_test_data(self):
        """Fetch all test data from the database."""
        with SessionLocal() as session:
            return pd.read_sql("SELECT * FROM test_code_generation", session.bind)

    def on_start(self):
        """Runs before the test starts."""
        self.db_session = SessionLocal()
        self.user = self.db_session.query(User).filter_by(username="test_user").first()
    
    def on_stop(self):
        """Runs after the test finishes - Generates the Excel report."""
        df = self.get_test_data()
        with pd.ExcelWriter("test_code_generation_report.xlsx", engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Full Data", index=False)



    @task
    def send_data_via_webhook(self):
        """
        Simulates sending data to the webhook.
        """
        if not self.tasks_executed:
            start_time = time.time()  # Start timing
            
            payload = {
                "created_by": self.user.username if self.user else "user",
                "action": "generate_code"
            }

            with self.client.post(
                "https://webhooks.fivetran.com/webhooks/615b5e5c-9fde-4c75-a034-f642dba74c1f",
                json=payload,
                catch_response=True
            ) as response:
                end_time = time.time()  # End timing

                if response.status_code == 200:
                    response.success()  # Mark request as successful
                    print(response.text)

                    self.environment.events.request.fire(
                        request_type="HTTP",
                        name="send_data_via_webhook",
                        response_time=(end_time - start_time) * 1000,  # Convert to milliseconds
                        response_length=len(response.content),
                        exception=None,
                    )

                    db_session = SessionLocal()
                    try:
                        code = generate_sequential_code(db_session, created_by=self.user.username if self.user else "user")
                    except Exception as e:
                        response.failure(f"Database error: {e}")
                    finally:
                        db_session.close()
                else:
                    response.failure(f"Request failed with status {response.status_code}")

            self.tasks_executed = True
