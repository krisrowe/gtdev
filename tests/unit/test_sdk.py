from gtdev import sdk
import os

def test_init_creates_config_directory():
    """Verify that init_workspace creates the configuration directory in the isolated path."""
    config_dir = sdk.get_config_dir()
    
    # Pre-condition: dir should not exist yet in the isolated tmp path
    assert not config_dir.exists()
    
    # Action
    sdk.init_workspace()
    
    # Post-condition
    assert config_dir.exists()
    assert config_dir.is_dir()
