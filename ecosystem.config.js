module.exports = {
    apps: [
        {
            name: "gbleagues-bot",
            script: "main.py",
            interpreter: "/home/jordanvps/amapicks/venv/bin/python",
            cwd: "/home/jordanvps/amapicks",
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
            log_file: "/home/jordanvps/amapicks/logs/bot-combined.log",
            out_file: "/home/jordanvps/amapicks/logs/bot-out.log",
            error_file: "/home/jordanvps/amapicks/logs/bot-error.log",
            log_date_format: "YYYY-MM-DD HH:mm:ss Z",
            merge_logs: true,
            time: true
        },
        {
            name: "gbleagues-backend",
            script: "/home/jordanvps/amapicks/venv/bin/python",
            args: "-m uvicorn main:app --host 0.0.0.0 --port 8001",
            cwd: "/home/jordanvps/amapicks/web/backend",
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
            log_file: "/home/jordanvps/amapicks/logs/backend-combined.log",
            out_file: "/home/jordanvps/amapicks/logs/backend-out.log",
            error_file: "/home/jordanvps/amapicks/logs/backend-error.log",
            log_date_format: "YYYY-MM-DD HH:mm:ss Z",
            merge_logs: true,
            time: true
        },
        {
            name: "gbleagues-frontend",
            script: "npx",
            args: "serve dist -l 5173 -s",
            cwd: "/home/jordanvps/amapicks/web/frontend",
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
            log_file: "/home/jordanvps/amapicks/logs/frontend-combined.log",
            out_file: "/home/jordanvps/amapicks/logs/frontend-out.log",
            error_file: "/home/jordanvps/amapicks/logs/frontend-error.log",
            log_date_format: "YYYY-MM-DD HH:mm:ss Z",
            merge_logs: true,
            time: true
        }
    ]
};
