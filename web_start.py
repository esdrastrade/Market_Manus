"""
Starter script para interface web do Market Manus
"""
from web_interface.app import run_web_server

if __name__ == '__main__':
    run_web_server(host='0.0.0.0', port=5000, debug=False)
