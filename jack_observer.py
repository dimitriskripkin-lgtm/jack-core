import re

BAD_PATTERNS = [
    "command not found", "permission denied", "syntax error",
    "traceback", "fatal", "exception", "error:"
]

def check_output(stdout_str, stderr_str):
    combined = (str(stdout_str) + " " + str(stderr_str)).lower()
    found = [p for p in BAD_PATTERNS if p in combined]
    return len(found) == 0, found

if __name__ == "__main__":
    ok, errs = check_output("bash: foo: command not found", "")
    print(f"Observer Test: OK={ok}, Errs={errs}")
