Client2 frontend for Internship Finder

- Open `client2/index.html` in a browser (or serve it with a simple static server).
- Backend expected at `http://127.0.0.1:5000/api` with endpoints:
  - `GET /api/internships` - list internships (optional query `q`, `category`)
  - `POST /api/internships` - create internship (requires `Authorization: Bearer <token>`)
  - `POST /api/signup` - create account (returns `auth_token`)
  - `POST /api/login` - login (returns `auth_token`)
  - `GET/POST /api/tracker` - manage trackers (requires token)

Notes:
- Frontend stores `auth_token` in `localStorage`.
- Use the existing Flask backend in `server/` and run it separately.
