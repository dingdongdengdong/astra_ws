

configs.py: Provides structured configurations for robots, including Astra variants (astra, astra_joint, astra_cart), with safety features and mock mode support.
astra.py: Implements the AstraRobot class, enabling teleoperation, observation capture, and action execution via the AstraController.
utils.py: Offers factory functions for creating robot configurations and instances, ensuring consistency and ease of use within LeRobot.


These scripts collectively enable the LeRobot framework to manage the Astra robot (and others) with configurability, safety, and a clear interface for interaction. The Astra-specific configurations and class are tailored to support joint space control, with Cartesian space marked as a future extension.