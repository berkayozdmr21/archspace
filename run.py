"""Start the packaged studio without requiring Node.js."""
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).absolute().parent

def main():
    if not (ROOT / 'frontend/dist/index.html').exists():
        raise SystemExit('Frontend missing. Run npm ci && npm run build in frontend.')
    with socket.socket() as probe:
        try:
            probe.bind(('127.0.0.1', 8980))
        except OSError:
            probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    url = f'http://127.0.0.1:{port}'
    process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', str(port)], cwd=ROOT)
    try:
        for _ in range(100):
            if process.poll() is not None:
                raise SystemExit('Server stopped. See the error above.')
            try:
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                with opener.open(url + '/api/health', timeout=1) as response:
                    if response.status == 200:
                        print('\nArchSpace: ' + url + '\nKeep this window open. Ctrl+C stops the studio.\n', flush=True)
                        webbrowser.open(url)
                        break
            except OSError:
                time.sleep(.2)
        else:
            raise SystemExit('Server did not become ready. See the error above.')
        process.wait()
    except KeyboardInterrupt:
        pass
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=10)

if __name__ == '__main__':
    main()
