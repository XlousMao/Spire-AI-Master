import sys
import os

# 将 external 目录添加到路径，以便导入其中的库 (如果需要手动源码引用)
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'external'))

def main():
    print("Spire AI Master is starting...")
    print("Please ensure communication with CommunicationMod is established.")
    # TODO: Initialize UI and Agent here

if __name__ == "__main__":
    main()
