from movie_generator import SystemIntegrator
import asyncio

async def test_movie_generation():
    # Initialize the system
    config = {
        "api_key": "your_api_key",
        "mongodb_uri": "mongodb://localhost:27017",
        "database_name": "movie_generator_test"
    }
    
    system = SystemIntegrator(config)
    await system.initialize_system()

    # Create a test project
    project_data = {
        "title": "Forest Adventure",
        "description": "A short animated story about woodland creatures",
        "type": "animation",
        "requirements": {
            "style": "animated",
            "duration": 60,  # seconds
            "target_audience": "children",
            "theme": "nature",
            "mood": "cheerful"
        },
        "story_elements": {
            "characters": ["rabbit", "fox", "owl"],
            "setting": "forest",
            "time_of_day": "morning",
            "weather": "sunny"
        }
    }

    # Start the project
    project_id = await system.create_project(project_data)
    print(f"Created project with ID: {project_id}")

    # Monitor progress
    while True:
        status = await system.get_project_status(project_id)
        print(f"Status: {status['status']}, Progress: {status['progress']}%")
        
        if status['status'] in ['completed', 'failed']:
            break
            
        await asyncio.sleep(5)  # Check every 5 seconds

    # Export if completed
    if status['status'] == 'completed':
        export_result = await system.export_project(
            project_id,
            format="mp4",
            output_path="./output/test_movie.mp4"
        )
        print(f"Export completed: {export_result}")

    await system.shutdown_system()

if __name__ == "__main__":
    asyncio.run(test_movie_generation()) 