# Contributing to Sound2Target

Thanks for your interest in contributing! 🎉

## How to Contribute

### 🐛 Report Bugs

Open an issue with:
- What you expected
- What actually happened
- Steps to reproduce
- Your environment (OS, Python version, browser)

### 💡 Suggest Features

Open an issue with:
- The problem you're trying to solve
- Your proposed solution
- Alternatives you've considered

### 🔧 Submit Code

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Test locally: `cd S2T/tests && pytest`
5. Commit: `git commit -m "feat: add xxx"`
6. Push and open a Pull Request

### 📝 Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation
- `refactor:` — Code refactor
- `test:` — Add tests
- `chore:` — Maintenance

### 🏗️ Project Structure

```
S2T/
├── backend/          # FastAPI (Python)
│   ├── api/          # REST routes
│   ├── core/         # ASR, LLM, Audio engines
│   ├── models/       # SQLite models
│   └── config/       # Configuration
├── frontend/         # Vue 3 + Element Plus
│   └── src/
│       ├── views/    # Pages
│       ├── components/
│       └── api/      # API client
└── tests/            # pytest tests
```

### ⚙️ Development Setup

```bash
# Backend (with hot-reload)
cd S2T/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (with HMR)
cd S2T/frontend
npm install
npm run dev
```

### 🧪 Running Tests

```bash
cd S2T/tests
pip install -r requirements.txt
pytest -v
```

## Questions?

Open an issue or start a discussion. We're friendly! 😊
