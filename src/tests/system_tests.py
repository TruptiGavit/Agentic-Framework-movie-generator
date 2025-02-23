import asyncio
import pytest
from typing import Dict, Any
import logging
from pathlib import Path

from src.core.system_integrator import SystemIntegrator
from src.core.message_bus import Message

class TestSystemIntegration:
    """System integration tests."""
    
    @pytest.fixture
    async def system(self):
        """System fixture."""
        system = SystemIntegrator("test_config")
        await system.initialize_system()
        yield system
        await system.shutdown_system()
    
    @pytest.mark.asyncio
    async def test_system_initialization(self, system):
        """Test system initialization."""
        assert system.is_running
        assert system.agent_manager.agents
        assert system.message_bus.is_running
        assert system.task_scheduler.is_running
    
    @pytest.mark.asyncio
    async def test_project_creation(self, system):
        """Test project creation and pipeline."""
        project_data = {
            "title": "Test Project",
            "description": "A test animation project",
            "requirements": {
                "style": "animated",
                "duration": 60,
                "target_audience": "general"
            },
            "scenes": [
                {
                    "scene_id": "scene_1",
                    "description": "Opening scene with character introduction",
                    "duration": 10
                }
            ]
        }
        
        project_id = await system.create_project(project_data)
        assert project_id in system.active_projects
        assert system.active_projects[project_id]["status"] == "initializing"
    
    @pytest.mark.asyncio
    async def test_story_pipeline(self, system):
        """Test story generation pipeline."""
        scene_data = {
            "scene_id": "test_scene",
            "description": "A character walks through a forest",
            "requirements": {
                "mood": "peaceful",
                "time_of_day": "morning"
            }
        }
        
        # Test plot generation
        plot_message = Message(
            message_id="test_plot",
            sender="test",
            receiver="plot_generator",
            message_type="generate_plot",
            content={"scene_data": scene_data}
        )
        
        response = await system.agent_manager.send_message_to_agent(
            "plot_generator",
            plot_message
        )
        assert response and response.message_type == "plot_generated"
    
    @pytest.mark.asyncio
    async def test_visual_pipeline(self, system):
        """Test visual generation pipeline."""
        scene_data = {
            "scene_id": "test_scene",
            "plot": {
                "description": "Character walking animation",
                "style": "cartoon"
            }
        }
        
        # Test scene interpretation
        interpret_message = Message(
            message_id="test_interpret",
            sender="test",
            receiver="scene_interpreter",
            message_type="interpret_scene",
            content={"scene_data": scene_data}
        )
        
        response = await system.agent_manager.send_message_to_agent(
            "scene_interpreter",
            interpret_message
        )
        assert response and response.message_type == "scene_interpreted"
    
    @pytest.mark.asyncio
    async def test_audio_pipeline(self, system):
        """Test audio generation pipeline."""
        scene_data = {
            "scene_id": "test_scene",
            "audio_requirements": {
                "music": "ambient",
                "effects": ["footsteps", "wind"],
                "dialogue": ["character_1: Hello there!"]
            }
        }
        
        # Test music composition
        music_message = Message(
            message_id="test_music",
            sender="test",
            receiver="music_composer",
            message_type="compose_music",
            content={"scene_data": scene_data}
        )
        
        response = await system.agent_manager.send_message_to_agent(
            "music_composer",
            music_message
        )
        assert response and response.message_type == "music_composed"
    
    @pytest.mark.asyncio
    async def test_quality_pipeline(self, system):
        """Test quality control pipeline."""
        project_data = {
            "project_id": "test_project",
            "scenes": [{
                "scene_id": "test_scene",
                "content": {
                    "visual": {"quality": "high"},
                    "audio": {"quality": "high"}
                }
            }]
        }
        
        # Test continuity checking
        continuity_message = Message(
            message_id="test_continuity",
            sender="test",
            receiver="continuity_checker",
            message_type="check_continuity",
            content={"project_data": project_data}
        )
        
        response = await system.agent_manager.send_message_to_agent(
            "continuity_checker",
            continuity_message
        )
        assert response and response.message_type == "continuity_checked"
    
    @pytest.mark.asyncio
    async def test_error_handling(self, system):
        """Test system error handling."""
        # Trigger an error
        error_message = Message(
            message_id="test_error",
            sender="test",
            receiver="non_existent_agent",
            message_type="invalid_operation",
            content={}
        )
        
        # Error should be caught and handled
        await system.agent_manager.send_message_to_agent(
            "non_existent_agent",
            error_message
        )
        
        # Check error was logged
        assert len(system.error_handler.active_errors) > 0
    
    @pytest.mark.asyncio
    async def test_system_shutdown(self, system):
        """Test system shutdown."""
        await system.shutdown_system()
        assert not system.is_running
        assert not system.message_bus.is_running
        assert not system.task_scheduler.is_running 