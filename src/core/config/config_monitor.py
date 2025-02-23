from typing import Dict, Any, Optional, Callable, Set
import asyncio
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from .config_manager import ConfigManager

class ConfigEventHandler(FileSystemEventHandler):
    """Handles configuration file system events."""
    
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.logger = logging.getLogger(__name__)
        
        # Track modified files to handle duplicate events
        self._modified_files: Set[str] = set()
        self._debounce_delay = 1.0  # seconds
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not isinstance(event, FileModifiedEvent):
            return
            
        file_path = Path(event.src_path)
        if file_path.suffix == '.yaml':
            config_type = file_path.stem
            
            # Debounce multiple events for the same file
            if config_type not in self._modified_files:
                self._modified_files.add(config_type)
                asyncio.create_task(self._handle_modification(config_type))
    
    async def _handle_modification(self, config_type: str):
        """Handle file modification with debouncing."""
        try:
            await asyncio.sleep(self._debounce_delay)
            self._modified_files.remove(config_type)
            self.callback(config_type)
            
        except Exception as e:
            self.logger.error(f"Error handling config modification: {str(e)}")

class ConfigMonitor:
    """Monitors configuration files for changes and triggers reloads."""
    
    def __init__(self, config_manager: ConfigManager):
        self.logger = logging.getLogger(__name__)
        self.config_manager = config_manager
        self.config_dir = config_manager.config_dir
        
        # Initialize event handler and observer
        self.event_handler = ConfigEventHandler(self._handle_config_change)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, str(self.config_dir), recursive=False)
        
        # Track active reload tasks
        self._reload_tasks: Dict[str, asyncio.Task] = {}
        
        # Event for signaling configuration changes
        self.config_changed_event = asyncio.Event()
        
        # Callback registry
        self.change_callbacks: Dict[str, Set[Callable]] = {
            "system": set(),
            "agents": set(),
            "pipeline": set(),
            "resources": set()
        }
    
    async def start(self):
        """Start configuration monitoring."""
        try:
            self.logger.info("Starting configuration monitor...")
            self.observer.start()
            
            # Start background monitoring task
            asyncio.create_task(self._monitor_changes())
            
        except Exception as e:
            self.logger.error(f"Failed to start configuration monitor: {str(e)}")
            raise
    
    async def stop(self):
        """Stop configuration monitoring."""
        try:
            self.logger.info("Stopping configuration monitor...")
            self.observer.stop()
            self.observer.join()
            
            # Cancel any pending reload tasks
            for task in self._reload_tasks.values():
                if not task.done():
                    task.cancel()
            
        except Exception as e:
            self.logger.error(f"Failed to stop configuration monitor: {str(e)}")
            raise
    
    def register_callback(self, config_type: str, callback: Callable):
        """Register callback for configuration changes."""
        if config_type in self.change_callbacks:
            self.change_callbacks[config_type].add(callback)
    
    def unregister_callback(self, config_type: str, callback: Callable):
        """Unregister callback for configuration changes."""
        if config_type in self.change_callbacks:
            self.change_callbacks[config_type].discard(callback)
    
    def _handle_config_change(self, config_type: str):
        """Handle configuration file changes."""
        # Cancel existing reload task if any
        if config_type in self._reload_tasks:
            existing_task = self._reload_tasks[config_type]
            if not existing_task.done():
                existing_task.cancel()
        
        # Create new reload task
        self._reload_tasks[config_type] = asyncio.create_task(
            self._reload_and_notify(config_type)
        )
        
        # Set the change event
        self.config_changed_event.set()
    
    async def _reload_and_notify(self, config_type: str):
        """Reload configuration and notify callbacks."""
        try:
            # Reload configuration
            updated_config = await self.config_manager.reload_config(config_type)
            
            # Notify callbacks
            for callback in self.change_callbacks.get(config_type, []):
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(updated_config)
                    else:
                        callback(updated_config)
                except Exception as e:
                    self.logger.error(f"Error in config change callback: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Error reloading configuration {config_type}: {str(e)}")
        finally:
            # Cleanup task reference
            self._reload_tasks.pop(config_type, None)
    
    async def _monitor_changes(self):
        """Background task to monitor configuration changes."""
        while True:
            try:
                # Wait for configuration changes
                await self.config_changed_event.wait()
                self.config_changed_event.clear()
                
                # Check for any pending reload tasks
                pending_tasks = [task for task in self._reload_tasks.values() 
                               if not task.done()]
                
                if pending_tasks:
                    # Wait for all pending reloads to complete
                    await asyncio.gather(*pending_tasks, return_exceptions=True)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in configuration monitor: {str(e)}")
                await asyncio.sleep(1)  # Prevent tight error loop 