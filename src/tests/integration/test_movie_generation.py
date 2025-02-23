import pytest
import asyncio
from movie_generator import SystemIntegrator
from movie_generator.core.errors import SystemInitializationError

@pytest.mark.asyncio
async def test_full_movie_generation():
    """Test complete movie generation pipeline."""
    system = SystemIntegrator()
    
    try:
        await system.initialize_system()
        
        project_data = {
            "title": "Test Movie",
            "description": "Integration test movie",
            "requirements": {
                "style": "animated",
                "duration": 30,
                "target_audience": "general"
            }
        }
        
        project_id = await system.create_project(project_data)
        assert project_id is not None
        
        # Monitor progress
        max_wait_time = 600  # 10 minutes
        start_time = asyncio.get_event_loop().time()
        
        while True:
            status = await system.get_project_status(project_id)
            if status["status"] == "completed":
                break
            elif status["status"] == "failed":
                pytest.fail(f"Project failed: {status['errors']}")
            elif asyncio.get_event_loop().time() - start_time > max_wait_time:
                pytest.fail("Project timed out")
            await asyncio.sleep(5)
            
        # Verify outputs
        result = await system.export_project(project_id, "mp4")
        assert result["success"] is True
        assert result["output_path"].exists()
        
    finally:
        await system.shutdown_system() 