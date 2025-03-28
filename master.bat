@echo off
echo Starting Locust in Master Mode...
locust -f "D:\Temp_Proj\QA App\QA-App-finalize_sessions\uploads\web_result_single-.py" --host=http://localhost --web-port 8088 --master
pause