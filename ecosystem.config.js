module.exports = {
    apps: [
        {
            name: "amapicks-bot",
            script: "main.py",
            interpreter: "/home/amarelita/amapicks/venv/bin/python",
            cwd: "/home/amarelita/amapicks",
            watch: false,
            autorestart: true,
            max_restarts: 10,
            restart_delay: 5000,
            max_memory_restart: "512M",
            kill_timeout: 5000,
            env: {
                NODE_ENV: "production"
            },
            env_production: {
                NODE_ENV: "production"
            },
            log_file: "/home/amarelita/amapicks/logs/bot-combined.log",
            out_file: "/home/amarelita/amapicks/logs/bot-out.log",
            error_file: "/home/amarelita/amapicks/logs/bot-error.log",
            log_date_format: "YYYY-MM-DD HH:mm:ss Z",
            merge_logs: true,
            time: true
        },
        {
            name: "amapicks-backend",
            script: "/home/amarelita/amapicks/venv/bin/python",
            args: "-m uvicorn main:app --host 0.0.0.0 --port 8001",
            cwd: "/home/amarelita/amapicks/web/backend",
            watch: false,
            autorestart: true,
            max_restarts: 10,
            restart_delay: 3000,
            max_memory_restart: "512M",
            kill_timeout: 5000,
            env: {
                NODE_ENV: "production"
            },
            env_production: {
                NODE_ENV: "production"
            },
            log_file: "/home/amarelita/amapicks/logs/backend-combined.log",
            out_file: "/home/amarelita/amapicks/logs/backend-out.log",
            error_file: "/home/amarelita/amapicks/logs/backend-error.log",
            log_date_format: "YYYY-MM-DD HH:mm:ss Z",
            merge_logs: true,
            time: true
        },
        {
            name: "amapicks-frontend",
            script: "npx",
            args: "serve dist -l 5173 -s",
            cwd: "/home/amarelita/amapicks/web/frontend",
            watch: false,
            autorestart: true,
            max_restarts: 5,
            restart_delay: 3000,
            max_memory_restart: "256M",
            kill_timeout: 5000,
            env: {
                NODE_ENV: "production"
            },
            env_production: {
                NODE_ENV: "production"
            },
            log_file: "/home/amarelita/amapicks/logs/frontend-combined.log",
            out_file: "/home/amarelita/amapicks/logs/frontend-out.log",
            error_file: "/home/amarelita/amapicks/logs/frontend-error.log",
            log_date_format: "YYYY-MM-DD HH:mm:ss Z",
            merge_logs: true,
            time: true
        }
    ]
};
