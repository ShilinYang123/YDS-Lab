import sys
import os
from unittest.mock import MagicMock, Mock

# Mock external dependencies that might not be installed
sys.modules['cv2'] = MagicMock()
sys.modules['pyautogui'] = MagicMock()
sys.modules['pystray'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['PIL.Image'] = MagicMock()
sys.modules['PIL.ImageTk'] = MagicMock()

# Mock internal services
image_service_mock = MagicMock()
image_service_mock.update_config = MagicMock()
click_service_mock = MagicMock()
click_service_mock.update_config = MagicMock()
process_service_mock = MagicMock()
process_service_mock.update_config = MagicMock()

sys.modules['src.services.image_recognition_service'] = MagicMock()
sys.modules['src.services.image_recognition_service'].ImageRecognitionService = MagicMock(return_value=image_service_mock)

sys.modules['src.services.click_service'] = MagicMock()
sys.modules['src.services.click_service'].AutoClickService = MagicMock(return_value=click_service_mock)

sys.modules['src.services.process_service'] = MagicMock()
sys.modules['src.services.process_service'].ProcessMonitorService = MagicMock(return_value=process_service_mock)

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))