import subprocess
import sys
import os

def run_cmd(cmd, cwd=None):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True, cwd=cwd)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def auto_update():
    """
    Checks for updates and applies them. 
    Returns True if an update was applied, False otherwise.
    """
    # Assuming meow.py is in src/hekerbot/meow.py, the repo root is 3 levels up
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    
    # Verify it's a git repo
    if not os.path.exists(os.path.join(repo_root, ".git")):
        return False
        
    print("[*] Checking for updates...")
    
    # Fetch latest from remote
    _, stderr, rc = run_cmd("git fetch", cwd=repo_root)
    if rc != 0:
        return False

    # Get local and remote commit hashes
    local_hash, _, rc_local = run_cmd("git rev-parse HEAD", cwd=repo_root)
    remote_hash, _, rc_remote = run_cmd("git rev-parse @{u}", cwd=repo_root)

    behind_str, _, rc_behind = run_cmd("git rev-list HEAD..@{u} --count", cwd=repo_root)
    
    if rc_local != 0 or rc_remote != 0 or rc_behind != 0:
        return False

    if behind_str == "0":
        print("[+] HekerBOT is up to date.")
        return None
        
    print(f"[*] Updating from current hash {local_hash[:7]} to new hash {remote_hash[:7]}...")
    
    status_out, _, _ = run_cmd("git status --porcelain", cwd=repo_root)
    has_changes = len(status_out) > 0
    
    if has_changes:
        run_cmd("git stash", cwd=repo_root)
    
    stdout, stderr, rc = run_cmd("git pull", cwd=repo_root)
    
    if has_changes:
        run_cmd("git stash pop", cwd=repo_root)
        
    if rc != 0:
        print(f"[-] Failed to pull updates: {stderr}")
        return None
    
    print("[*] Reinstalling to ensure dependencies are up to date...")
    
    # Re-install project
    if subprocess.run("which uv", shell=True, capture_output=True).returncode == 0:
        cmd = "uv pip install -e ."
    else:
        cmd = "pip install -e ."
        
    result = subprocess.run(cmd, shell=True, cwd=repo_root)
    if result.returncode != 0:
        print(f"[-] Failed to install dependencies!")
        return None
        
    print("[+] HekerBOT has been updated successfully!")
    return (local_hash[:7], remote_hash[:7])
