import os
import sys
from typing import Optional

class InstanceLock:
    def __init__(self, lockfile: str = "bot.lock"):
        self.lockfile = lockfile
        self.fd: Optional[int] = None

    def acquire(self) -> bool:
        try:
            if sys.platform == "win32":
                # Реализация для Windows
                if os.path.exists(self.lockfile):
                    return False
                with open(self.lockfile, 'w') as f:
                    f.write(str(os.getpid()))
                return True
            else:
                # Реализация для Linux/Mac
                import fcntl  # type: ignore
                self.fd = os.open(self.lockfile, os.O_CREAT | os.O_WRONLY)
                try:
                    fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return True
                except (IOError, BlockingIOError):
                    return False
        except Exception as e:
            print(f"Lock error: {e}")
            return False

    def release(self):
        try:
            if sys.platform == "win32":
                if os.path.exists(self.lockfile):
                    os.unlink(self.lockfile)
            elif self.fd:
                import fcntl  # type: ignore
                fcntl.flock(self.fd, fcntl.LOCK_UN)
                os.close(self.fd)
                try:
                    os.unlink(self.lockfile)
                except:
                    pass
        except Exception as e:
            print(f"Unlock error: {e}")