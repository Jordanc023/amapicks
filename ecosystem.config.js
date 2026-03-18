module.exports = {
    apps: [
        {
            name: "amapicks-bot",
            script: "main.py",
            interpreter: "/home/jordanvps/amapicks/venv/bin/python",
            cwd: "/home/jordanvps/amapicks",
            watch: false,
            autorestart: true,
            max_restarts: 10,
            restart_delay: 5000,
            env: {
                // Environment variables are loaded from .env file
            }
        },
        {
            name: "amapicks-backend",
            script: "/home/jordanvps/amapicks/venv/bin/python",
            args: "-m uvicorn main:app --host 0.0.0.0 --port 8001",
            cwd: "/home/jordanvps/amapicks/web/backend",
            watch: false,
            autorestart: true,
            env: {
                // Environment variables
            }
        },
        {
            name: "amapicks-frontend",
            script: "npm",
            args: "run dev -- --host 0.0.0.0",
            cwd: "/home/jordanvps/amapicks/web/frontend",
            watch: false,
            autorestart: true,
            env: {
                // Environment variables
            }
        }
    ]
};
