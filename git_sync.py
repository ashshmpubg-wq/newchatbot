import os
import asyncio
import logging


async def _run(cmd: list[str]) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    out, err = await proc.communicate()
    return proc.returncode, out.decode(errors="ignore"), err.decode(errors="ignore")


async def sync_database_to_github(commit_message: str = "Baza yangilandi"):
    if not os.getenv("GITHUB_ACTIONS"):
        return
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPOSITORY")
    if not token or not repo:
        logging.warning("[GIT-SYNC] GITHUB_TOKEN yoki GITHUB_REPOSITORY topilmadi")
        return

    remote_url = f"https://x-access-token:{token}@github.com/{repo}.git"
    steps = [
        ["git", "config", "user.email", "bot@users.noreply.github.com"],
        ["git", "config", "user.name", "Telegram Bot"],
        ["git", "remote", "set-url", "origin", remote_url],
        ["git", "add", "database.db"],
        ["git", "commit", "-m", commit_message],
    ]
    for cmd in steps:
        code, out, err = await _run(cmd)
        if code != 0 and cmd[1] == "commit":
            logging.info(f"[GIT-SYNC] Commit qilinmadi: {err.strip()}")
            return

    code, out, err = await _run(["git", "push"])
    if code != 0:
        await _run(["git", "pull", "--rebase", "-X", "ours"])
        code, out, err = await _run(["git", "push"])
        if code != 0:
            logging.error(f"[GIT-SYNC] Push muvaffaqiyatsiz: {err.strip()}")
            return
    logging.info("[GIT-SYNC] database.db saqlandi")
