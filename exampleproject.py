import asyncio
from movie_generator import SystemIntegrator
from pathlib import Path

async def create_simple_animation():
    # Initialize the system
    system = SystemIntegrator()
    await system.initialize_system()
    
    # Project configuration
    project_data = {
        "title": "Forest Adventure",
        "description": "A short animated story about woodland creatures",
        "requirements": {
            "style": "animated",
            "duration": 60,
            "target_audience": "children",
            "theme": "nature",
            "mood": "cheerful"
        },
        "story_elements": {
            "characters": [
                {
                    "name": "Pip",
                    "type": "squirrel",
                    "personality": "adventurous"
                },
                {
                    "name": "Luna",
                    "type": "owl",
                    "personality": "wise"
                }
            ],
            "settings": [
                {
                    "name": "Forest Clearing",
                    "time": "morning",
                    "weather": "sunny"
                }
            ]
        },
        "technical_requirements": {
            "resolution": "1920x1080",
            "framerate": 30,
            "audio_quality": "high"
        }
    }
    
    # Create project
    project_id = await system.create_project(project_data)
    print(f"Created project: {project_id}")
    
    # Monitor progress
    while True:
        status = await system.get_project_status(project_id)
        print(f"Status: {status['current_stage']} - {status['progress']}%")
        
        if status["status"] == "completed":
            break
            
        await asyncio.sleep(5)
    
    # Export result
    output_path = Path("output/forest_adventure.mp4")
    await system.export_project(project_id, format="mp4", output_path=output_path)
    print(f"Project exported to: {output_path}")

if __name__ == "__main__":
    asyncio.run(create_simple_animation())
