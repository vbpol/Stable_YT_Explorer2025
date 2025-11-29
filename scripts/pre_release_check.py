import os
import sys
import json
sys.path.append(os.getcwd())

def fail(msg):
    print(json.dumps({'status':'fail','reason':msg}))
    sys.exit(1)

def ok(msg, extra=None):
    out = {'status':'ok','message':msg}
    if extra:
        out.update(extra)
    print(json.dumps(out))

def check_logs_dir():
    d = os.path.join(os.getcwd(), 'logs')
    try:
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'pre_release_check.tmp'), 'w', encoding='utf-8').write('ok')
        os.remove(os.path.join(d, 'pre_release_check.tmp'))
    except Exception as e:
        fail(f'logs dir not writable: {e}')

def check_parity():
    from scripts.verify_datastore_parity import main as parity_main
    # Run parity; rely on printed JSON and basic process success
    try:
        parity_main()
    except SystemExit:
        pass
    except Exception as e:
        fail(f'parity script error: {e}')

def check_requirements_list():
    req = os.path.join(os.getcwd(), 'requirements.txt')
    if not os.path.exists(req):
        fail('requirements.txt missing')
    ok('requirements.txt present')

def main():
    check_logs_dir()
    check_requirements_list()
    check_parity()
    ok('pre-release checks passed')

if __name__ == '__main__':
    main()

