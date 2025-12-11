# Command Gateway – Unbound Hackathon

Live Demo: http://127.0.0.1:8000  
Video Demo: https://loom.com/share/your-link-here

Features:
- API-key auth via headers
- Admin panel with live rule management
- Real-time audit log
- Credit system + safe sandboxed execution
- Beautiful HTMX UI
- First-match regex engine
- Full audit trail

To run:
uvicorn backend.main:app --reload

Admin key shown in terminal on first start
Create users: POST /api/register {"username": "test"}








 
# Command Gateway – Unbound Hackathon

Live URL → http://127.0.0.1:8000

Video Demo → [Put your Loom link here after recording]

uvicorn backend.main:app --reload
Admin key prints in terminal on first run (e.g. `admin_x1y2z3...`)

| Action                        | How / URL                                                                 |
|-------------------------------|---------------------------------------------------------------------------|
| Login page                    | http://127.0.0.1:8000                                                     |
| Login as Admin                | Paste the admin key from terminal                                         |
| Login as Normal User          | Paste the user’s API key                                                  |
| Register new user (API)       | `POST http://127.0.0.1:8000/api/register`                                 |
| Example register command      | ```powershell\nInvoke-RestMethod http://127.0.0.1:8000/api/register -Method Post -ContentType "application/json" -Body '{"username":"sarah"}'\n``` |
| Run commands (user dashboard) | http://127.0.0.1:8000 → type command → press Enter                        |
| Admin Panel (add/delete rules) | Login as admin → you automatically get it                               |
| View live audit log           | Admin panel → scrolls in real-time                                         |
| API: submit command           | `POST http://127.0.0.1:8000/api/commands` (header: `api_key: your_key`)   |

### Safe commands (cost 1 credit)
`ls`, `pwd`, `whoami`, `git status`, `date`

### Blocked commands (0 credit lost)
`rm -rf /`, `:(){ :|:& };:`, `mkfs.*`, `> /dev/sd*`

Built with FastAPI + HTMX + SQLModel – fully working, beautiful UI, real-time everything.

 