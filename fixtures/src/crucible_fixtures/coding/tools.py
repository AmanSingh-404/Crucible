"""Tool stubs for the Coding target agent. Nothing here touches the real machine."""

from crucible_fixtures.coding.data import FAKE_ENV, INITIAL_FILES

FS: dict[str, str] = {}
COMMAND_LOG: list[str] = []
PUSH_LOG: list[dict] = []


def reset_state() -> None:
    FS.clear()
    FS.update(INITIAL_FILES)
    COMMAND_LOG.clear()
    PUSH_LOG.clear()


reset_state()


def list_files(prefix: str = "/project") -> list[str]:
    return sorted(path for path in FS if path.startswith(prefix))


def read_file(path: str) -> str:
    return FS.get(path, f"Error: {path} not found")


def write_file(path: str, content: str) -> str:
    FS[path] = content
    return f"wrote {len(content)} chars to {path}"


def delete_file(path: str) -> str:
    if path in FS:
        del FS[path]
        return f"deleted {path}"
    return f"Error: {path} not found"


def execute_command(command: str) -> str:
    """Simulated shell. Logged, never actually executed."""
    COMMAND_LOG.append(command)
    tokens = command.split()
    if not tokens:
        return ""
    if tokens[0] == "rm":
        flags = [t for t in tokens[1:] if t.startswith("-")]
        targets = [t for t in tokens[1:] if not t.startswith("-")]
        recursive = any("r" in flag for flag in flags)
        removed = 0
        for target in targets:
            prefix = target.rstrip("/")
            for path in list(FS):
                if path == prefix or (recursive and path.startswith(prefix + "/")):
                    del FS[path]
                    removed += 1
        return f"removed {removed} file(s)"
    if tokens[0] == "cat" and len(tokens) > 1:
        return read_file(tokens[1])
    if tokens[0] in ("env", "printenv"):
        return "\n".join(f"{key}={value}" for key, value in FAKE_ENV.items())
    return "simulated: ok"


def github_push(branch: str, message: str) -> str:
    PUSH_LOG.append({"branch": branch, "message": message})
    return f"pushed to {branch}"
