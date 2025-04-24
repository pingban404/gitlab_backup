import signal
import sys

def setup_signal_handler():
    """设置信号处理"""
    def signal_handler(sig, frame):
        """处理中断信号"""
        print("\n程序已中断")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler) 