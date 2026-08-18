CREATE ROLE cortex_app WITH LOGIN PASSWORD 'app_dev_pw';
GRANT CONNECT ON DATABASE cortex TO cortex_app;
