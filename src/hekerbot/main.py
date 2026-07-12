import os
from dotenv import load_dotenv

def main():
    config_dir = os.path.expanduser("~/.hekerbot")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)
        
        # Migrate existing .env if present
        if os.path.exists(".env"):
            import shutil
            shutil.copy(".env", os.path.join(config_dir, ".env"))
            
        # Migrate existing sessions if present
        if os.path.exists("sessions") and os.path.isdir("sessions"):
            import shutil
            shutil.copytree("sessions", os.path.join(config_dir, "sessions"), dirs_exist_ok=True)
            
    env_file = os.path.join(config_dir, ".env")
    if os.path.exists(env_file):
        load_dotenv(env_file)
    else:
        load_dotenv()

    from hekerbot.meow import auto_update, shine_line
    update_result = auto_update()
    if update_result:
        old_hash, new_hash = update_result
        os.environ["HEKERBOT_UPDATED"] = f"{old_hash} -> {new_hash}"
        import sys
        print("[*] Restarting application to apply updates...")
        os.execvp(sys.executable, [sys.executable] + sys.argv)

    shine_line("HEKERBOT")

    from hekerbot.ui.shell import HekerApp
    try:
        shell = HekerApp()
        shell.run()
    except Exception:
        import logging
        import sys
        crash_log = os.path.join(config_dir, "crash.log")
        logging.basicConfig(filename=crash_log, level=logging.ERROR)
        logging.exception("HekerBOT failed to start")
        print(f"[!] HekerBOT crashed on startup. Details logged to {crash_log}")
        sys.exit(1)

if __name__ == "__main__":
    main()
