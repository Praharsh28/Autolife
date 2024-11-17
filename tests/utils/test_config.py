"""Tests for the config module."""

import pytest
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import shutil

from modules.utils.config import (
    Config,
    load_config,
    save_config,
    get_config,
    update_config,
    CONFIG_FILE,
    DEFAULT_CONFIG
)

@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for config files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def sample_config():
    """Create a sample configuration."""
    return {
        'app_name': 'AutoLife',
        'version': '1.0.0',
        'debug': True,
        'paths': {
            'media': '/path/to/media',
            'subtitles': '/path/to/subtitles',
            'output': '/path/to/output'
        },
        'processing': {
            'threads': 4,
            'gpu_enabled': True,
            'batch_size': 32
        },
        'ui': {
            'theme': 'dark',
            'language': 'en',
            'font_size': 12
        }
    }

@pytest.fixture
def config_file(temp_config_dir, sample_config):
    """Create a temporary config file."""
    config_path = temp_config_dir / "config.json"
    with open(config_path, 'w') as f:
        json.dump(sample_config, f)
    return config_path

class TestConfig:
    """Test cases for config module."""

    @pytest.mark.config
    def test_config_initialization(self, sample_config):
        """Test configuration initialization."""
        config = Config(sample_config)
        
        assert config.data == sample_config
        assert config.get('app_name') == 'AutoLife'
        assert config.get('version') == '1.0.0'

    @pytest.mark.config
    def test_load_config(self, config_file, sample_config):
        """Test loading configuration from file."""
        config = load_config(config_file)
        
        assert isinstance(config, Config)
        assert config.data == sample_config
        assert config.get('paths.media') == '/path/to/media'

    @pytest.mark.config
    def test_save_config(self, temp_config_dir, sample_config):
        """Test saving configuration to file."""
        config_path = temp_config_dir / "test_config.json"
        config = Config(sample_config)
        
        save_config(config, config_path)
        
        # Verify saved config
        with open(config_path, 'r') as f:
            saved_config = json.load(f)
            assert saved_config == sample_config

    @pytest.mark.config
    def test_get_config(self, config_file, sample_config):
        """Test getting configuration singleton."""
        config1 = get_config(config_file)
        config2 = get_config(config_file)
        
        # Should return same instance
        assert config1 is config2
        assert config1.data == sample_config

    @pytest.mark.config
    def test_update_config(self, config_file):
        """Test updating configuration values."""
        config = get_config(config_file)
        
        # Update values
        updates = {
            'debug': False,
            'paths.output': '/new/output/path',
            'processing.threads': 8
        }
        
        update_config(config, updates)
        
        # Verify updates
        assert config.get('debug') is False
        assert config.get('paths.output') == '/new/output/path'
        assert config.get('processing.threads') == 8

    @pytest.mark.config
    def test_nested_config_access(self, sample_config):
        """Test accessing nested configuration values."""
        config = Config(sample_config)
        
        assert config.get('paths.media') == '/path/to/media'
        assert config.get('processing.gpu_enabled') is True
        assert config.get('ui.theme') == 'dark'

    @pytest.mark.config
    def test_default_values(self):
        """Test default configuration values."""
        config = Config({})
        
        # Verify defaults match DEFAULT_CONFIG
        for key, value in DEFAULT_CONFIG.items():
            assert config.get(key) == value

    @pytest.mark.config
    def test_config_validation(self, sample_config):
        """Test configuration validation."""
        # Test invalid paths
        invalid_config = sample_config.copy()
        invalid_config['paths']['media'] = None
        
        with pytest.raises(ValueError):
            Config(invalid_config)
        
        # Test invalid processing settings
        invalid_config = sample_config.copy()
        invalid_config['processing']['threads'] = -1
        
        with pytest.raises(ValueError):
            Config(invalid_config)

    @pytest.mark.config
    def test_config_persistence(self, temp_config_dir, sample_config):
        """Test configuration persistence across saves and loads."""
        config_path = temp_config_dir / "persist_config.json"
        
        # Save initial config
        config1 = Config(sample_config)
        save_config(config1, config_path)
        
        # Load and modify
        config2 = load_config(config_path)
        update_config(config2, {'debug': False})
        save_config(config2, config_path)
        
        # Load again and verify
        config3 = load_config(config_path)
        assert config3.get('debug') is False

    @pytest.mark.config
    def test_config_merge(self, sample_config):
        """Test merging configurations."""
        base_config = Config(sample_config)
        
        # Create updates
        updates = {
            'paths': {
                'cache': '/path/to/cache',
                'media': '/updated/media/path'
            },
            'processing': {
                'gpu_device': 0
            }
        }
        
        update_config(base_config, updates)
        
        # Verify merged config
        assert base_config.get('paths.cache') == '/path/to/cache'
        assert base_config.get('paths.media') == '/updated/media/path'
        assert base_config.get('processing.gpu_device') == 0
        assert base_config.get('processing.threads') == 4  # Original value preserved

    @pytest.mark.config
    def test_error_handling(self, temp_config_dir):
        """Test error handling in config operations."""
        non_existent_file = temp_config_dir / "nonexistent.json"
        
        # Test loading non-existent file
        with pytest.raises(FileNotFoundError):
            load_config(non_existent_file)
        
        # Test invalid JSON
        invalid_json_file = temp_config_dir / "invalid.json"
        with open(invalid_json_file, 'w') as f:
            f.write("invalid json content")
        
        with pytest.raises(json.JSONDecodeError):
            load_config(invalid_json_file)

    @pytest.mark.config
    def test_config_type_validation(self, sample_config):
        """Test configuration type validation."""
        config = Config(sample_config)
        
        # Test invalid types
        with pytest.raises(TypeError):
            update_config(config, {'processing.threads': '4'})  # Should be int
        
        with pytest.raises(TypeError):
            update_config(config, {'debug': 'true'})  # Should be bool

    @pytest.mark.config
    def test_config_backup(self, temp_config_dir, sample_config):
        """Test configuration backup functionality."""
        config_path = temp_config_dir / "backup_config.json"
        backup_path = config_path.with_suffix('.json.bak')
        
        # Save initial config
        config = Config(sample_config)
        save_config(config, config_path)
        
        # Create backup
        shutil.copy(config_path, backup_path)
        
        # Modify and save
        update_config(config, {'debug': False})
        save_config(config, config_path)
        
        # Verify backup preserved
        with open(backup_path, 'r') as f:
            backup_config = json.load(f)
            assert backup_config['debug'] is True  # Original value
