# envctl

> CLI tool to manage and switch between environment variable profiles for multiple projects

---

## Installation

```bash
pip install envctl
```

Or install from source:

```bash
git clone https://github.com/yourusername/envctl.git && cd envctl && pip install .
```

---

## Usage

```bash
# Create a new profile
envctl create myproject/production

# Set environment variables in a profile
envctl set myproject/production DATABASE_URL=postgres://localhost/mydb

# Switch to a profile (exports vars into current shell)
envctl use myproject/production

# List all profiles
envctl list

# Show variables in a profile
envctl show myproject/production

# Delete a profile
envctl delete myproject/production
```

Profiles are stored locally in `~/.envctl/` and never leave your machine.

---

## Why envctl?

- 🔀 Instantly switch between `dev`, `staging`, and `production` configs
- 📁 Organize profiles per project
- 🔒 Keeps secrets local — no cloud sync, no leaks
- ⚡ Lightweight with zero runtime dependencies

---

## License

MIT © [yourusername](https://github.com/yourusername)