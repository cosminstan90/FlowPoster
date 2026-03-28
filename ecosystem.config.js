module.exports = {
  apps: [
    // ── FastAPI backend ──────────────────────────────────────────────────────
    {
      name: 'flowposter-api',
      script: '/home/flowposter/app/venv/bin/uvicorn',
      args: 'backend.main:app --host 127.0.0.1 --port 8050 --workers 2',
      cwd: '/home/flowposter/app',
      interpreter: 'none',   // uvicorn is its own executable, not a node script
      exec_mode: 'fork',
      env: {
        PYTHONPATH: '/home/flowposter/app',
      },
      max_memory_restart: '400M',
      error_file: '/home/flowposter/logs/api-error.log',
      out_file: '/home/flowposter/logs/api-out.log',
      time: true,
      kill_timeout: 10000,
      autorestart: true,
      watch: false,
    },

    // ── ARQ background worker (job queue + hourly scheduler) ────────────────
    {
      name: 'flowposter-worker',
      script: '/home/flowposter/app/venv/bin/python',
      args: '-m arq backend.worker.worker_settings.WorkerSettings',
      cwd: '/home/flowposter/app',
      interpreter: 'none',
      exec_mode: 'fork',
      env: {
        PYTHONPATH: '/home/flowposter/app',
      },
      max_memory_restart: '300M',
      error_file: '/home/flowposter/logs/worker-error.log',
      out_file: '/home/flowposter/logs/worker-out.log',
      time: true,
      // Give the worker time to finish in-flight jobs before killing
      kill_timeout: 30000,
      autorestart: true,
      watch: false,
    },
  ],
};
