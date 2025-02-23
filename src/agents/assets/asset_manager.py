from typing import Optional, Dict, Any, List
from src.core.base_agent import BaseAgent, Message
import hashlib
import shutil
from pathlib import Path
import json
import aiofiles
from datetime import datetime
import PIL.Image
import numpy as np
import bpy
import wave
import audioop
import os

class AssetManager(BaseAgent):
    """Agent responsible for managing and organizing project assets."""
    
    def __init__(self, agent_id: str):
        super().__init__(agent_id)
        self.asset_registry: Dict[str, Any] = {}
        self.version_history: Dict[str, List[Dict[str, Any]]] = {}
        self.asset_cache: Dict[str, Any] = {}
        self.asset_config = {
            "base_path": Path("assets"),
            "cache_path": Path("cache/assets"),
            "max_versions": 5,
            "supported_types": {
                "model": [".fbx", ".obj", ".blend"],
                "texture": [".png", ".jpg", ".exr"],
                "audio": [".wav", ".mp3"],
                "animation": [".fbx", ".bvh"]
            }
        }
    
    async def process_message(self, message: Message) -> Optional[Message]:
        if message.message_type == "register_asset":
            return await self._register_asset(message)
        elif message.message_type == "get_asset":
            return await self._get_asset(message)
        elif message.message_type == "update_asset":
            return await self._update_asset(message)
        elif message.message_type == "optimize_asset":
            return await self._optimize_asset(message)
        elif message.message_type == "batch_process_assets":
            return await self.batch_process_assets(message)
        elif message.message_type == "validate_dependencies":
            return await self.validate_dependencies(message)
        elif message.message_type == "export_assets":
            return await self.export_assets(message)
        elif message.message_type == "import_assets":
            return await self.import_assets(message)
        elif message.message_type == "synchronize_assets":
            return await self.synchronize_assets(message)
        elif message.message_type == "verify_asset_integrity":
            return await self.verify_asset_integrity(message)
        return None
    
    async def _register_asset(self, message: Message) -> Message:
        """Register a new asset in the system."""
        asset_data = message.content.get("asset_data", {})
        asset_type = message.content.get("asset_type", "")
        
        registration_result = await self._process_asset_registration(asset_data, asset_type)
        
        return Message(
            message_id=f"reg_{message.message_id}",
            sender=self.agent_id,
            receiver=message.sender,
            message_type="asset_registered",
            content={"registration_result": registration_result},
            context=message.context,
            metadata={"asset_type": asset_type}
        )
    
    async def _process_asset_registration(self, asset_data: Dict[str, Any], asset_type: str) -> Dict[str, Any]:
        """Process and register a new asset."""
        try:
            # Generate unique asset ID
            asset_id = self._generate_asset_id(asset_data)
            
            # Validate asset type and file format
            if not self._validate_asset_type(asset_data, asset_type):
                raise ValueError(f"Invalid asset type or format: {asset_type}")
            
            # Create asset directory structure
            asset_path = self._create_asset_directory(asset_id, asset_type)
            
            # Copy asset files to managed location
            file_paths = await self._copy_asset_files(asset_data, asset_path)
            
            # Register asset metadata
            metadata = self._create_asset_metadata(asset_data, asset_id, asset_type, file_paths)
            self.asset_registry[asset_id] = metadata
            
            # Initialize version history
            self.version_history[asset_id] = [{
                "version": 1,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata,
                "changes": "Initial version"
            }]
            
            # Save registry updates
            await self._save_asset_registry()
            
            return {
                "asset_id": asset_id,
                "status": "success",
                "metadata": metadata
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _generate_asset_id(self, asset_data: Dict[str, Any]) -> str:
        """Generate unique asset ID based on content and metadata."""
        content = json.dumps(asset_data, sort_keys=True).encode()
        return hashlib.sha256(content).hexdigest()[:12]
    
    def _validate_asset_type(self, asset_data: Dict[str, Any], asset_type: str) -> bool:
        """Validate asset type and file format."""
        if asset_type not in self.asset_config["supported_types"]:
            return False
        
        file_path = Path(asset_data.get("file_path", ""))
        return file_path.suffix.lower() in self.asset_config["supported_types"][asset_type]
    
    def _create_asset_directory(self, asset_id: str, asset_type: str) -> Path:
        """Create directory structure for asset storage."""
        asset_path = self.asset_config["base_path"] / asset_type / asset_id
        asset_path.mkdir(parents=True, exist_ok=True)
        return asset_path
    
    async def _copy_asset_files(self, asset_data: Dict[str, Any], asset_path: Path) -> Dict[str, str]:
        """Copy asset files to managed location."""
        source_path = Path(asset_data.get("file_path", ""))
        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        destination_path = asset_path / source_path.name
        shutil.copy2(source_path, destination_path)
        
        return {
            "main": str(destination_path),
            "dependencies": await self._copy_dependencies(asset_data, asset_path)
        }
    
    async def _copy_dependencies(self, asset_data: Dict[str, Any], asset_path: Path) -> Dict[str, str]:
        """Copy asset dependencies."""
        dependencies = {}
        for dep in asset_data.get("dependencies", []):
            source = Path(dep["path"])
            if source.exists():
                dest = asset_path / "dependencies" / source.name
                dest.parent.mkdir(exist_ok=True)
                shutil.copy2(source, dest)
                dependencies[dep["type"]] = str(dest)
        return dependencies
    
    def _create_asset_metadata(self, asset_data: Dict[str, Any], asset_id: str, 
                             asset_type: str, file_paths: Dict[str, str]) -> Dict[str, Any]:
        """Create asset metadata record."""
        return {
            "id": asset_id,
            "type": asset_type,
            "name": asset_data.get("name", ""),
            "description": asset_data.get("description", ""),
            "file_paths": file_paths,
            "properties": asset_data.get("properties", {}),
            "tags": asset_data.get("tags", []),
            "created_at": datetime.now().isoformat(),
            "modified_at": datetime.now().isoformat(),
            "version": 1
        }
    
    async def _optimize_asset(self, message: Message) -> Message:
        """Optimize asset for better performance."""
        asset_id = message.content.get("asset_id", "")
        optimization_type = message.content.get("optimization_type", "all")
        
        if asset_id not in self.asset_registry:
            return Message(
                message_id=f"opt_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="asset_optimization_failed",
                content={"error": "Asset not found"},
                context=message.context
            )
        
        optimization_result = await self._optimize_asset_files(asset_id, optimization_type)
        
        return Message(
            message_id=f"opt_{message.message_id}",
            sender=self.agent_id,
            receiver=message.sender,
            message_type="asset_optimized",
            content={"optimization_result": optimization_result},
            context=message.context
        )
    
    async def _optimize_asset_files(self, asset_id: str, optimization_type: str) -> Dict[str, Any]:
        """Optimize asset files based on type and requirements."""
        asset = self.asset_registry[asset_id]
        asset_type = asset["type"]
        optimizations = []

        try:
            if optimization_type in ["all", "size"]:
                size_opt = await self._optimize_file_size(asset)
                optimizations.extend(size_opt)
            
            if asset_type == "model" and optimization_type in ["all", "model"]:
                model_opt = await self._optimize_model(asset)
                optimizations.extend(model_opt)
            
            elif asset_type == "texture" and optimization_type in ["all", "texture"]:
                texture_opt = await self._optimize_texture(asset)
                optimizations.extend(texture_opt)
            
            elif asset_type == "audio" and optimization_type in ["all", "audio"]:
                audio_opt = await self._optimize_audio(asset)
                optimizations.extend(audio_opt)

            # Update asset version after optimization
            await self._create_new_version(asset_id, "Optimization", optimizations)
            
            return {
                "status": "success",
                "optimizations": optimizations,
                "asset_id": asset_id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "asset_id": asset_id
            }

    async def _optimize_model(self, asset: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optimize 3D model assets."""
        optimizations = []
        model_path = Path(asset["file_paths"]["main"])
        
        # Load model into Blender
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        
        if model_path.suffix == ".blend":
            bpy.ops.wm.open_mainfile(filepath=str(model_path))
        else:
            if model_path.suffix == ".fbx":
                bpy.ops.import_scene.fbx(filepath=str(model_path))
            elif model_path.suffix == ".obj":
                bpy.ops.import_scene.obj(filepath=str(model_path))
        
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                # Optimize mesh
                original_verts = len(obj.data.vertices)
                
                # Apply modifiers
                ctx = bpy.context.copy()
                ctx['object'] = obj
                bpy.ops.object.convert(ctx, target='MESH')
                
                # Remove doubles
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.remove_doubles()
                bpy.ops.object.mode_set(mode='OBJECT')
                
                # Decimate if necessary
                if len(obj.data.vertices) > 10000:
                    decimate = obj.modifiers.new(name="Decimate", type='DECIMATE')
                    decimate.ratio = 0.5
                    bpy.ops.object.modifier_apply(modifier="Decimate")
                
                optimizations.append({
                    "type": "mesh_optimization",
                    "object": obj.name,
                    "original_vertices": original_verts,
                    "optimized_vertices": len(obj.data.vertices)
                })
        
        # Save optimized model
        optimized_path = model_path.parent / f"optimized_{model_path.name}"
        bpy.ops.wm.save_as_mainfile(filepath=str(optimized_path))
        
        return optimizations

    async def _optimize_texture(self, asset: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optimize texture assets."""
        optimizations = []
        texture_path = Path(asset["file_paths"]["main"])
        
        with PIL.Image.open(texture_path) as img:
            original_size = img.size
            original_mode = img.mode
            
            # Convert to more efficient color mode if possible
            if img.mode == 'RGBA' and not self._needs_alpha(img):
                img = img.convert('RGB')
            
            # Resize if too large
            if max(img.size) > 4096:
                aspect_ratio = img.size[0] / img.size[1]
                if img.size[0] > img.size[1]:
                    new_size = (4096, int(4096 / aspect_ratio))
                else:
                    new_size = (int(4096 * aspect_ratio), 4096)
                img = img.resize(new_size, PIL.Image.LANCZOS)
            
            # Optimize and save
            optimized_path = texture_path.parent / f"optimized_{texture_path.name}"
            img.save(optimized_path, optimize=True, quality=85)
            
            optimizations.append({
                "type": "texture_optimization",
                "original_size": original_size,
                "optimized_size": img.size,
                "original_mode": original_mode,
                "optimized_mode": img.mode
            })
        
        return optimizations

    async def _optimize_audio(self, asset: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optimize audio assets."""
        optimizations = []
        audio_path = Path(asset["file_paths"]["main"])
        
        with wave.open(str(audio_path), 'rb') as wav:
            # Get original parameters
            original_params = {
                "channels": wav.getnchannels(),
                "sampwidth": wav.getsampwidth(),
                "framerate": wav.getframerate(),
                "frames": wav.getnframes()
            }
            
            # Read audio data
            audio_data = wav.readframes(wav.getnframes())
            
            # Optimize parameters
            target_framerate = 44100  # CD quality
            if original_params["framerate"] > target_framerate:
                # Downsample
                audio_data, _ = audioop.ratecv(
                    audio_data,
                    original_params["sampwidth"],
                    original_params["channels"],
                    original_params["framerate"],
                    target_framerate,
                    None
                )
            
            # Save optimized audio
            optimized_path = audio_path.parent / f"optimized_{audio_path.name}"
            with wave.open(str(optimized_path), 'wb') as opt_wav:
                opt_wav.setnchannels(original_params["channels"])
                opt_wav.setsampwidth(original_params["sampwidth"])
                opt_wav.setframerate(target_framerate)
                opt_wav.writeframes(audio_data)
            
            optimizations.append({
                "type": "audio_optimization",
                "original_params": original_params,
                "optimized_params": {
                    "channels": original_params["channels"],
                    "sampwidth": original_params["sampwidth"],
                    "framerate": target_framerate
                }
            })
        
        return optimizations

    async def _create_new_version(self, asset_id: str, change_type: str, changes: List[Dict[str, Any]]) -> None:
        """Create a new version of an asset."""
        asset = self.asset_registry[asset_id]
        current_version = asset["version"]
        
        # Create new version metadata
        new_version = {
            "version": current_version + 1,
            "timestamp": datetime.now().isoformat(),
            "change_type": change_type,
            "changes": changes,
            "metadata": {**asset, "version": current_version + 1}
        }
        
        # Update version history
        self.version_history[asset_id].append(new_version)
        
        # Maintain maximum versions
        if len(self.version_history[asset_id]) > self.asset_config["max_versions"]:
            self.version_history[asset_id].pop(0)
        
        # Update current asset metadata
        self.asset_registry[asset_id] = new_version["metadata"]
        
        # Save registry updates
        await self._save_asset_registry()

    def _needs_alpha(self, img: PIL.Image.Image) -> bool:
        """Check if image needs alpha channel."""
        if 'A' not in img.mode:
            return False
        
        # Check if alpha channel is being used
        alpha = img.split()[-1]
        return alpha.getextrema()[0] < 255
    
    async def _save_asset_registry(self) -> None:
        """Save asset registry to disk."""
        registry_file = self.asset_config["base_path"] / "registry.json"
        async with aiofiles.open(registry_file, 'w') as f:
            await f.write(json.dumps({
                "assets": self.asset_registry,
                "versions": self.version_history
            }, indent=2))
    
    async def initialize(self) -> None:
        """Initialize asset management system."""
        # Create necessary directories
        self.asset_config["base_path"].mkdir(parents=True, exist_ok=True)
        self.asset_config["cache_path"].mkdir(parents=True, exist_ok=True)
        
        # Load existing asset registry
        await self._load_asset_registry()
    
    async def cleanup(self) -> None:
        """Cleanup asset management resources."""
        # Save final state of asset registry
        await self._save_asset_registry()
        
        # Clear caches
        self.asset_cache.clear()
        shutil.rmtree(self.asset_config["cache_path"], ignore_errors=True)

    async def _get_asset(self, message: Message) -> Message:
        """Retrieve an asset from the system."""
        asset_id = message.content.get("asset_id", "")
        load_type = message.content.get("load_type", "metadata")  # metadata, full, cached
        
        try:
            if load_type == "cached" and asset_id in self.asset_cache:
                asset_data = self.asset_cache[asset_id]
            else:
                asset_data = await self._load_asset(asset_id, load_type)
            
            return Message(
                message_id=f"get_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="asset_retrieved",
                content={"asset_data": asset_data},
                context=message.context
            )
        except Exception as e:
            return Message(
                message_id=f"get_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="asset_retrieval_failed",
                content={"error": str(e)},
                context=message.context
            )

    async def _load_asset(self, asset_id: str, load_type: str) -> Dict[str, Any]:
        """Load asset data based on load type."""
        if asset_id not in self.asset_registry:
            raise ValueError(f"Asset not found: {asset_id}")
        
        metadata = self.asset_registry[asset_id]
        
        if load_type == "metadata":
            return metadata
        
        # Load full asset data
        asset_data = {
            "metadata": metadata,
            "versions": self.version_history.get(asset_id, []),
            "files": await self._load_asset_files(metadata)
        }
        
        # Cache the asset if it's not too large
        if await self._should_cache_asset(asset_data):
            self.asset_cache[asset_id] = asset_data
        
        return asset_data

    async def _load_asset_files(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Load asset files based on type."""
        asset_type = metadata["type"]
        file_paths = metadata["file_paths"]
        
        if asset_type == "model":
            return await self._load_model_files(file_paths)
        elif asset_type == "texture":
            return await self._load_texture_files(file_paths)
        elif asset_type == "audio":
            return await self._load_audio_files(file_paths)
        else:
            return await self._load_generic_files(file_paths)

    async def search_assets(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search assets based on query parameters."""
        results = []
        
        asset_type = query.get("type")
        tags = query.get("tags", [])
        name_query = query.get("name", "").lower()
        properties = query.get("properties", {})
        
        for asset_id, metadata in self.asset_registry.items():
            if self._matches_search_criteria(metadata, asset_type, tags, name_query, properties):
                results.append(metadata)
        
        # Sort results by relevance
        results.sort(key=lambda x: self._calculate_relevance(x, query))
        
        return results

    def _matches_search_criteria(self, metadata: Dict[str, Any], 
                               asset_type: Optional[str], 
                               tags: List[str], 
                               name_query: str,
                               properties: Dict[str, Any]) -> bool:
        """Check if asset matches search criteria."""
        # Type check
        if asset_type and metadata["type"] != asset_type:
            return False
        
        # Name check
        if name_query and name_query not in metadata["name"].lower():
            return False
        
        # Tags check
        if tags and not all(tag in metadata["tags"] for tag in tags):
            return False
        
        # Properties check
        asset_props = metadata.get("properties", {})
        for key, value in properties.items():
            if key not in asset_props or asset_props[key] != value:
                return False
        
        return True

    def _calculate_relevance(self, metadata: Dict[str, Any], query: Dict[str, Any]) -> float:
        """Calculate search result relevance score."""
        score = 0.0
        
        # Exact type match
        if query.get("type") == metadata["type"]:
            score += 1.0
        
        # Tag matches
        query_tags = query.get("tags", [])
        metadata_tags = set(metadata["tags"])
        if query_tags:
            tag_match_ratio = len([tag for tag in query_tags if tag in metadata_tags]) / len(query_tags)
            score += tag_match_ratio
        
        # Name similarity
        name_query = query.get("name", "").lower()
        if name_query:
            name_similarity = self._calculate_string_similarity(name_query, metadata["name"].lower())
            score += name_similarity * 2.0  # Weight name matches more heavily
        
        return score

    def _calculate_string_similarity(self, s1: str, s2: str) -> float:
        """Calculate simple string similarity score."""
        if s1 in s2 or s2 in s1:
            return 0.8
        
        # Count common substrings
        common = sum(1 for i in range(min(len(s1), len(s2))) if s1[i] == s2[i])
        return common / max(len(s1), len(s2))

    async def _should_cache_asset(self, asset_data: Dict[str, Any]) -> bool:
        """Determine if asset should be cached based on size and type."""
        try:
            metadata = asset_data["metadata"]
            asset_type = metadata["type"]
            
            # Always cache small assets
            if asset_type in ["texture", "audio"]:
                file_size = Path(metadata["file_paths"]["main"]).stat().st_size
                return file_size < 50 * 1024 * 1024  # 50MB limit
            
            # Cache models based on complexity
            if asset_type == "model":
                return len(asset_data.get("files", {}).get("vertices", [])) < 100000
            
            return True
        except Exception:
            return False

    async def preload_assets(self, asset_ids: List[str]) -> None:
        """Preload assets into cache."""
        for asset_id in asset_ids:
            try:
                if asset_id not in self.asset_cache:
                    asset_data = await self._load_asset(asset_id, "full")
                    if await self._should_cache_asset(asset_data):
                        self.asset_cache[asset_id] = asset_data
            except Exception as e:
                print(f"Error preloading asset {asset_id}: {str(e)}")

    async def clear_cache(self, asset_ids: Optional[List[str]] = None) -> None:
        """Clear asset cache, optionally for specific assets only."""
        if asset_ids is None:
            self.asset_cache.clear()
        else:
            for asset_id in asset_ids:
                self.asset_cache.pop(asset_id, None)

    async def _update_asset(self, message: Message) -> Message:
        """Update an existing asset."""
        asset_id = message.content.get("asset_id", "")
        update_data = message.content.get("update_data", {})
        update_type = message.content.get("update_type", "modify")
        
        try:
            update_result = await self._process_asset_update(asset_id, update_data, update_type)
            
            return Message(
                message_id=f"update_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="asset_updated",
                content={"update_result": update_result},
                context=message.context
            )
        except Exception as e:
            return Message(
                message_id=f"update_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="asset_update_failed",
                content={"error": str(e)},
                context=message.context
            )

    async def _process_asset_update(self, asset_id: str, update_data: Dict[str, Any], update_type: str) -> Dict[str, Any]:
        """Process asset update and manage dependencies."""
        if asset_id not in self.asset_registry:
            raise ValueError(f"Asset not found: {asset_id}")
        
        asset = self.asset_registry[asset_id]
        
        # Track dependencies before update
        old_dependencies = await self._get_asset_dependencies(asset_id)
        
        # Apply update
        if update_type == "modify":
            updated_asset = await self._modify_asset(asset, update_data)
        elif update_type == "replace":
            updated_asset = await self._replace_asset(asset, update_data)
        else:
            raise ValueError(f"Invalid update type: {update_type}")
        
        # Track new dependencies
        new_dependencies = await self._get_asset_dependencies(asset_id)
        
        # Update dependency references
        await self._update_dependency_references(asset_id, old_dependencies, new_dependencies)
        
        # Create new version
        changes = [{
            "type": update_type,
            "timestamp": datetime.now().isoformat(),
            "details": update_data
        }]
        await self._create_new_version(asset_id, update_type, changes)
        
        return {
            "status": "success",
            "asset_id": asset_id,
            "update_type": update_type,
            "dependencies_changed": old_dependencies != new_dependencies
        }

    async def _get_asset_dependencies(self, asset_id: str) -> Dict[str, List[str]]:
        """Get all dependencies for an asset."""
        asset = self.asset_registry[asset_id]
        dependencies = {
            "direct": [],
            "indirect": [],
            "referenced_by": []
        }
        
        # Get direct dependencies
        for dep in asset.get("dependencies", []):
            dependencies["direct"].append(dep["asset_id"])
        
        # Get indirect dependencies recursively
        for dep_id in dependencies["direct"]:
            indirect_deps = await self._get_asset_dependencies(dep_id)
            dependencies["indirect"].extend(indirect_deps["direct"])
            dependencies["indirect"].extend(indirect_deps["indirect"])
        
        # Get assets that reference this asset
        for other_id, other_asset in self.asset_registry.items():
            if other_id != asset_id:
                other_deps = other_asset.get("dependencies", [])
                if any(dep["asset_id"] == asset_id for dep in other_deps):
                    dependencies["referenced_by"].append(other_id)
        
        return dependencies

    async def _update_dependency_references(self, asset_id: str, 
                                         old_deps: Dict[str, List[str]], 
                                         new_deps: Dict[str, List[str]]) -> None:
        """Update dependency references after asset changes."""
        # Remove old dependency references
        for dep_id in old_deps["direct"]:
            if dep_id not in new_deps["direct"]:
                dep_asset = self.asset_registry[dep_id]
                dep_asset.setdefault("referenced_by", []).remove(asset_id)
        
        # Add new dependency references
        for dep_id in new_deps["direct"]:
            if dep_id not in old_deps["direct"]:
                dep_asset = self.asset_registry[dep_id]
                dep_asset.setdefault("referenced_by", []).append(asset_id)
        
        # Save registry updates
        await self._save_asset_registry()

    async def batch_process_assets(self, message: Message) -> Message:
        """Process multiple assets in batch."""
        asset_ids = message.content.get("asset_ids", [])
        operation = message.content.get("operation", "")
        operation_params = message.content.get("operation_params", {})
        
        results = []
        failed = []
        
        for asset_id in asset_ids:
            try:
                if operation == "optimize":
                    result = await self._optimize_asset_files(asset_id, operation_params.get("optimization_type", "all"))
                elif operation == "update":
                    result = await self._process_asset_update(asset_id, operation_params.get("update_data", {}), 
                                                            operation_params.get("update_type", "modify"))
                else:
                    result = {"status": "error", "error": f"Unknown operation: {operation}"}
                
                if result["status"] == "success":
                    results.append({"asset_id": asset_id, **result})
                else:
                    failed.append({"asset_id": asset_id, **result})
                    
            except Exception as e:
                failed.append({
                    "asset_id": asset_id,
                    "status": "error",
                    "error": str(e)
                })
        
        return Message(
            message_id=f"batch_{message.message_id}",
            sender=self.agent_id,
            receiver=message.sender,
            message_type="batch_processing_complete",
            content={
                "successful": results,
                "failed": failed,
                "operation": operation
            },
            context=message.context
        )

    async def validate_dependencies(self, asset_id: str) -> List[Dict[str, Any]]:
        """Validate asset dependencies and check for issues."""
        issues = []
        
        try:
            dependencies = await self._get_asset_dependencies(asset_id)
            
            # Check for circular dependencies
            if asset_id in dependencies["indirect"]:
                issues.append({
                    "type": "circular_dependency",
                    "severity": "high",
                    "description": "Circular dependency detected",
                    "affected_assets": [asset_id] + dependencies["indirect"]
                })
            
            # Check for missing dependencies
            for dep_id in dependencies["direct"]:
                if dep_id not in self.asset_registry:
                    issues.append({
                        "type": "missing_dependency",
                        "severity": "high",
                        "description": f"Missing dependency: {dep_id}",
                        "dependency_id": dep_id
                    })
            
            # Check for version mismatches
            for dep_id in dependencies["direct"]:
                if dep_id in self.asset_registry:
                    dep_asset = self.asset_registry[dep_id]
                    if self._has_version_mismatch(asset_id, dep_id):
                        issues.append({
                            "type": "version_mismatch",
                            "severity": "medium",
                            "description": f"Version mismatch with dependency: {dep_id}",
                            "dependency_id": dep_id,
                            "current_version": dep_asset["version"]
                        })
        
        except Exception as e:
            issues.append({
                "type": "validation_error",
                "severity": "high",
                "description": f"Error validating dependencies: {str(e)}"
            })
        
        return issues

    def _has_version_mismatch(self, asset_id: str, dependency_id: str) -> bool:
        """Check for version mismatches between assets."""
        asset = self.asset_registry[asset_id]
        dependency = self.asset_registry[dependency_id]
        
        # Get the dependency version reference from the asset
        for dep in asset.get("dependencies", []):
            if dep["asset_id"] == dependency_id:
                return dep.get("version", 1) != dependency["version"]
        
        return False

    async def export_assets(self, message: Message) -> Message:
        """Export assets for distribution."""
        asset_ids = message.content.get("asset_ids", [])
        export_format = message.content.get("format", "package")  # package, archive, individual
        export_config = message.content.get("export_config", {})
        
        try:
            export_result = await self._process_asset_export(asset_ids, export_format, export_config)
            
            return Message(
                message_id=f"export_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="assets_exported",
                content={"export_result": export_result},
                context=message.context
            )
        except Exception as e:
            return Message(
                message_id=f"export_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="asset_export_failed",
                content={"error": str(e)},
                context=message.context
            )

    async def _process_asset_export(self, asset_ids: List[str], 
                                  export_format: str, 
                                  export_config: Dict[str, Any]) -> Dict[str, Any]:
        """Process asset export based on format and configuration."""
        export_path = Path(export_config.get("export_path", "exports"))
        export_path.mkdir(parents=True, exist_ok=True)
        
        if export_format == "package":
            return await self._create_asset_package(asset_ids, export_path, export_config)
        elif export_format == "archive":
            return await self._create_asset_archive(asset_ids, export_path, export_config)
        else:
            return await self._export_individual_assets(asset_ids, export_path, export_config)

    async def _create_asset_package(self, asset_ids: List[str], 
                                  export_path: Path,
                                  config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a self-contained asset package with metadata."""
        package_name = config.get("package_name", f"asset_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        package_path = export_path / package_name
        package_path.mkdir(exist_ok=True)
        
        exported_assets = []
        package_metadata = {
            "name": package_name,
            "created_at": datetime.now().isoformat(),
            "assets": [],
            "dependencies": {}
        }
        
        for asset_id in asset_ids:
            try:
                # Export asset and its dependencies
                asset_export = await self._export_asset_with_dependencies(
                    asset_id, package_path, package_metadata["dependencies"]
                )
                exported_assets.append(asset_export)
                package_metadata["assets"].append(asset_export["metadata"])
                
            except Exception as e:
                print(f"Error exporting asset {asset_id}: {str(e)}")
        
        # Save package metadata
        async with aiofiles.open(package_path / "package.json", 'w') as f:
            await f.write(json.dumps(package_metadata, indent=2))
        
        return {
            "package_path": str(package_path),
            "exported_assets": exported_assets,
            "metadata": package_metadata
        }

    async def _export_asset_with_dependencies(self, asset_id: str, 
                                            export_path: Path,
                                            dependency_map: Dict[str, Any]) -> Dict[str, Any]:
        """Export an asset and all its dependencies."""
        asset = self.asset_registry[asset_id]
        dependencies = await self._get_asset_dependencies(asset_id)
        
        # Export dependencies first
        exported_deps = []
        for dep_id in dependencies["direct"]:
            if dep_id not in dependency_map:
                dep_export = await self._export_single_asset(dep_id, export_path / "dependencies")
                dependency_map[dep_id] = dep_export["metadata"]
                exported_deps.append(dep_export)
        
        # Export main asset
        asset_export = await self._export_single_asset(asset_id, export_path / "assets")
        
        return {
            "asset_id": asset_id,
            "export_path": str(export_path),
            "metadata": asset_export["metadata"],
            "dependencies": exported_deps
        }

    async def _export_single_asset(self, asset_id: str, export_path: Path) -> Dict[str, Any]:
        """Export a single asset with its files."""
        asset = self.asset_registry[asset_id]
        asset_type = asset["type"]
        
        # Create asset directory
        asset_dir = export_path / asset_id
        asset_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy asset files
        exported_files = {}
        for file_type, file_path in asset["file_paths"].items():
            if file_type == "dependencies":
                continue
            
            source = Path(file_path)
            if source.exists():
                dest = asset_dir / source.name
                shutil.copy2(source, dest)
                exported_files[file_type] = str(dest.relative_to(export_path))
        
        # Create asset metadata
        export_metadata = {
            "id": asset_id,
            "type": asset_type,
            "name": asset["name"],
            "version": asset["version"],
            "exported_at": datetime.now().isoformat(),
            "files": exported_files
        }
        
        # Save metadata
        async with aiofiles.open(asset_dir / "metadata.json", 'w') as f:
            await f.write(json.dumps(export_metadata, indent=2))
        
        return {
            "asset_id": asset_id,
            "export_path": str(asset_dir),
            "metadata": export_metadata
        }

    async def _create_asset_archive(self, asset_ids: List[str], 
                                  export_path: Path,
                                  config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a compressed archive of assets."""
        import tarfile
        import zipfile
        
        archive_format = config.get("archive_format", "zip")
        archive_name = config.get("archive_name", f"assets_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Create temporary package
        package_result = await self._create_asset_package(asset_ids, export_path / "temp", config)
        package_path = Path(package_result["package_path"])
        
        # Create archive
        if archive_format == "zip":
            archive_path = export_path / f"{archive_name}.zip"
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in package_path.rglob('*'):
                    if file_path.is_file():
                        zf.write(file_path, file_path.relative_to(package_path))
        else:
            archive_path = export_path / f"{archive_name}.tar.gz"
            with tarfile.open(archive_path, 'w:gz') as tf:
                tf.add(package_path, arcname=archive_name)
        
        # Cleanup temporary files
        shutil.rmtree(package_path)
        
        return {
            "archive_path": str(archive_path),
            "archive_format": archive_format,
            "asset_count": len(asset_ids),
            "metadata": package_result["metadata"]
        }

    async def import_assets(self, message: Message) -> Message:
        """Import assets from a package or archive."""
        import_path = message.content.get("import_path", "")
        import_type = message.content.get("import_type", "auto")  # auto, package, archive
        import_config = message.content.get("import_config", {})
        
        try:
            import_result = await self._process_asset_import(import_path, import_type, import_config)
            
            return Message(
                message_id=f"import_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="assets_imported",
                content={"import_result": import_result},
                context=message.context
            )
        except Exception as e:
            return Message(
                message_id=f"import_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="asset_import_failed",
                content={"error": str(e)},
                context=message.context
            )

    async def _process_asset_import(self, import_path: str, 
                                  import_type: str, 
                                  import_config: Dict[str, Any]) -> Dict[str, Any]:
        """Process asset import based on type and configuration."""
        import_path = Path(import_path)
        if not import_path.exists():
            raise FileNotFoundError(f"Import path not found: {import_path}")
        
        if import_type == "auto":
            import_type = self._detect_import_type(import_path)
        
        if import_type == "archive":
            return await self._import_from_archive(import_path, import_config)
        else:
            return await self._import_from_package(import_path, import_config)

    def _detect_import_type(self, import_path: Path) -> str:
        """Detect the type of import based on the file or directory."""
        if import_path.is_file():
            if import_path.suffix in ['.zip', '.tar.gz']:
                return "archive"
        elif (import_path / "package.json").exists():
            return "package"
        
        raise ValueError(f"Unable to detect import type for: {import_path}")

    async def _import_from_archive(self, archive_path: Path, 
                                 config: Dict[str, Any]) -> Dict[str, Any]:
        """Import assets from an archive file."""
        import tempfile
        import tarfile
        import zipfile
        
        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract archive
            if archive_path.suffix == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zf:
                    zf.extractall(temp_path)
            else:
                with tarfile.open(archive_path, 'r:*') as tf:
                    tf.extractall(temp_path)
            
            # Find and import package
            package_file = next(temp_path.rglob("package.json"))
            return await self._import_from_package(package_file.parent, config)

    async def _import_from_package(self, package_path: Path, 
                                 config: Dict[str, Any]) -> Dict[str, Any]:
        """Import assets from a package directory."""
        # Load package metadata
        async with aiofiles.open(package_path / "package.json", 'r') as f:
            package_metadata = json.loads(await f.read())
        
        imported_assets = []
        failed_imports = []
        
        # Import dependencies first
        for dep_id, dep_metadata in package_metadata.get("dependencies", {}).items():
            try:
                dep_result = await self._import_single_asset(
                    package_path / "dependencies" / dep_id,
                    dep_metadata,
                    config
                )
                imported_assets.append(dep_result)
            except Exception as e:
                failed_imports.append({
                    "asset_id": dep_id,
                    "error": str(e)
                })
        
        # Import main assets
        for asset_metadata in package_metadata.get("assets", []):
            try:
                asset_result = await self._import_single_asset(
                    package_path / "assets" / asset_metadata["id"],
                    asset_metadata,
                    config
                )
                imported_assets.append(asset_result)
            except Exception as e:
                failed_imports.append({
                    "asset_id": asset_metadata["id"],
                    "error": str(e)
                })
        
        return {
            "imported_assets": imported_assets,
            "failed_imports": failed_imports,
            "package_metadata": package_metadata
        }

    async def _import_single_asset(self, asset_path: Path, 
                                 metadata: Dict[str, Any],
                                 config: Dict[str, Any]) -> Dict[str, Any]:
        """Import a single asset into the system."""
        asset_id = metadata["id"]
        asset_type = metadata["type"]
        
        # Check if asset already exists
        if asset_id in self.asset_registry:
            if not config.get("overwrite", False):
                raise ValueError(f"Asset already exists: {asset_id}")
        
        # Create asset directory in managed location
        managed_path = self.asset_config["base_path"] / asset_type / asset_id
        managed_path.mkdir(parents=True, exist_ok=True)
        
        # Copy asset files
        imported_files = {}
        for file_type, rel_path in metadata["files"].items():
            source = asset_path / Path(rel_path).name
            if source.exists():
                dest = managed_path / source.name
                shutil.copy2(source, dest)
                imported_files[file_type] = str(dest)
        
        # Create asset registration data
        asset_data = {
            "name": metadata["name"],
            "type": asset_type,
            "file_paths": imported_files,
            "properties": metadata.get("properties", {}),
            "tags": metadata.get("tags", [])
        }
        
        # Register the asset
        registration_result = await self._process_asset_registration(asset_data, asset_type)
        
        return {
            "asset_id": asset_id,
            "status": "success",
            "metadata": registration_result["metadata"]
        }

    async def synchronize_assets(self, message: Message) -> Message:
        """Synchronize assets with another system."""
        sync_target = message.content.get("sync_target", {})
        sync_mode = message.content.get("sync_mode", "pull")  # pull, push, bidirectional
        sync_config = message.content.get("sync_config", {})
        
        try:
            sync_result = await self._process_asset_sync(sync_target, sync_mode, sync_config)
            
            return Message(
                message_id=f"sync_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="assets_synchronized",
                content={"sync_result": sync_result},
                context=message.context
            )
        except Exception as e:
            return Message(
                message_id=f"sync_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="asset_sync_failed",
                content={"error": str(e)},
                context=message.context
            )

    async def _process_asset_sync(self, sync_target: Dict[str, Any], 
                                sync_mode: str,
                                sync_config: Dict[str, Any]) -> Dict[str, Any]:
        """Process asset synchronization with another system."""
        # Implementation would depend on the specific synchronization protocol
        # and communication method with the target system
        pass

    async def verify_asset_integrity(self, message: Message) -> Message:
        """Verify integrity of assets and identify any issues."""
        asset_ids = message.content.get("asset_ids", [])
        verification_type = message.content.get("verification_type", "all")
        
        try:
            verification_result = await self._verify_assets(asset_ids, verification_type)
            
            return Message(
                message_id=f"verify_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="assets_verified",
                content={"verification_result": verification_result},
                context=message.context
            )
        except Exception as e:
            return Message(
                message_id=f"verify_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="asset_verification_failed",
                content={"error": str(e)},
                context=message.context
            )

    async def _verify_assets(self, asset_ids: List[str], verification_type: str) -> Dict[str, Any]:
        """Perform asset verification checks."""
        verification_results = []
        repair_recommendations = []
        
        for asset_id in asset_ids:
            try:
                # Verify asset integrity
                asset_result = await self._verify_single_asset(asset_id, verification_type)
                verification_results.append(asset_result)
                
                # Generate repair recommendations if issues found
                if asset_result["issues"]:
                    repair_rec = self._generate_repair_recommendations(asset_id, asset_result["issues"])
                    repair_recommendations.extend(repair_rec)
                
            except Exception as e:
                verification_results.append({
                    "asset_id": asset_id,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "verification_results": verification_results,
            "repair_recommendations": repair_recommendations,
            "verification_type": verification_type
        }

    async def _verify_single_asset(self, asset_id: str, verification_type: str) -> Dict[str, Any]:
        """Verify integrity of a single asset."""
        if asset_id not in self.asset_registry:
            raise ValueError(f"Asset not found: {asset_id}")
        
        asset = self.asset_registry[asset_id]
        issues = []
        
        # File integrity checks
        if verification_type in ["all", "files"]:
            file_issues = await self._verify_file_integrity(asset)
            issues.extend(file_issues)
        
        # Metadata integrity checks
        if verification_type in ["all", "metadata"]:
            metadata_issues = self._verify_metadata_integrity(asset)
            issues.extend(metadata_issues)
        
        # Dependency integrity checks
        if verification_type in ["all", "dependencies"]:
            dependency_issues = await self._verify_dependency_integrity(asset_id)
            issues.extend(dependency_issues)
        
        # Format-specific checks
        if verification_type in ["all", "format"]:
            format_issues = await self._verify_format_integrity(asset)
            issues.extend(format_issues)
        
        return {
            "asset_id": asset_id,
            "status": "verified",
            "issues": issues,
            "verified_at": datetime.now().isoformat()
        }

    async def _verify_file_integrity(self, asset: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verify integrity of asset files."""
        issues = []
        
        for file_type, file_path in asset["file_paths"].items():
            path = Path(file_path)
            
            # Check file existence
            if not path.exists():
                issues.append({
                    "type": "missing_file",
                    "severity": "high",
                    "file_type": file_type,
                    "path": str(path),
                    "description": "Asset file is missing"
                })
                continue
            
            # Check file permissions
            if not os.access(path, os.R_OK):
                issues.append({
                    "type": "permission_error",
                    "severity": "high",
                    "file_type": file_type,
                    "path": str(path),
                    "description": "Cannot read asset file"
                })
            
            # Check file corruption
            try:
                if file_type == "main":
                    corruption_issues = await self._check_file_corruption(path, asset["type"])
                    issues.extend(corruption_issues)
            except Exception as e:
                issues.append({
                    "type": "corruption_check_error",
                    "severity": "medium",
                    "file_type": file_type,
                    "path": str(path),
                    "description": f"Error checking file corruption: {str(e)}"
                })
        
        return issues

    async def _check_file_corruption(self, file_path: Path, asset_type: str) -> List[Dict[str, Any]]:
        """Check for file corruption based on asset type."""
        issues = []
        
        try:
            if asset_type == "model":
                # Try loading the model file
                if file_path.suffix == ".blend":
                    bpy.ops.wm.open_mainfile(filepath=str(file_path))
                elif file_path.suffix == ".fbx":
                    bpy.ops.import_scene.fbx(filepath=str(file_path))
                elif file_path.suffix == ".obj":
                    bpy.ops.import_scene.obj(filepath=str(file_path))
            
            elif asset_type == "texture":
                # Try loading the image
                with PIL.Image.open(file_path) as img:
                    img.verify()
            
            elif asset_type == "audio":
                # Try loading the audio file
                with wave.open(str(file_path), 'rb') as wav:
                    wav.getparams()
        
        except Exception as e:
            issues.append({
                "type": "file_corruption",
                "severity": "high",
                "path": str(file_path),
                "description": f"File appears to be corrupted: {str(e)}"
            })
        
        return issues

    def _verify_metadata_integrity(self, asset: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verify integrity of asset metadata."""
        issues = []
        required_fields = ["id", "type", "name", "version", "file_paths"]
        
        # Check required fields
        for field in required_fields:
            if field not in asset:
                issues.append({
                    "type": "missing_metadata",
                    "severity": "high",
                    "field": field,
                    "description": f"Required metadata field '{field}' is missing"
                })
        
        # Check field types
        if not isinstance(asset.get("version", None), int):
            issues.append({
                "type": "invalid_metadata",
                "severity": "medium",
                "field": "version",
                "description": "Version must be an integer"
            })
        
        if not isinstance(asset.get("file_paths", None), dict):
            issues.append({
                "type": "invalid_metadata",
                "severity": "high",
                "field": "file_paths",
                "description": "file_paths must be a dictionary"
            })
        
        return issues

    def _generate_repair_recommendations(self, asset_id: str, 
                                       issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommendations for repairing asset issues."""
        recommendations = []
        
        for issue in issues:
            if issue["type"] == "missing_file":
                recommendations.append({
                    "asset_id": asset_id,
                    "issue_type": issue["type"],
                    "action": "restore",
                    "description": "Restore missing file from backup or re-import asset",
                    "automated_repair": False
                })
            
            elif issue["type"] == "file_corruption":
                recommendations.append({
                    "asset_id": asset_id,
                    "issue_type": issue["type"],
                    "action": "repair",
                    "description": "Attempt to repair corrupted file or restore from backup",
                    "automated_repair": True,
                    "repair_method": "restore_from_backup"
                })
            
            elif issue["type"] == "missing_metadata":
                recommendations.append({
                    "asset_id": asset_id,
                    "issue_type": issue["type"],
                    "action": "repair",
                    "description": f"Regenerate missing metadata field: {issue['field']}",
                    "automated_repair": True,
                    "repair_method": "regenerate_metadata"
                })
        
        return recommendations

    async def repair_asset(self, message: Message) -> Message:
        """Attempt to repair asset issues."""
        asset_id = message.content.get("asset_id", "")
        repair_type = message.content.get("repair_type", "")
        repair_config = message.content.get("repair_config", {})
        
        try:
            repair_result = await self._repair_asset_issues(asset_id, repair_type, repair_config)
            
            return Message(
                message_id=f"repair_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="asset_repaired",
                content={"repair_result": repair_result},
                context=message.context
            )
        except Exception as e:
            return Message(
                message_id=f"repair_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="asset_repair_failed",
                content={"error": str(e)},
                context=message.context
            )

    async def _repair_asset_issues(self, asset_id: str, 
                                 repair_type: str,
                                 repair_config: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to repair asset issues."""
        if repair_type == "restore_from_backup":
            return await self._restore_from_backup(asset_id, repair_config)
        elif repair_type == "regenerate_metadata":
            return await self._regenerate_metadata(asset_id, repair_config)
        elif repair_type == "repair_corruption":
            return await self._repair_file_corruption(asset_id, repair_config)
        else:
            raise ValueError(f"Unknown repair type: {repair_type}")

    async def _restore_from_backup(self, asset_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Restore asset from backup."""
        backup_path = self.asset_config["base_path"] / "backups" / asset_id
        if not backup_path.exists():
            raise FileNotFoundError(f"No backup found for asset: {asset_id}")
        
        # Find latest backup
        backup_versions = sorted([p for p in backup_path.iterdir() if p.is_dir()],
                               key=lambda p: p.name,
                               reverse=True)
        
        if not backup_versions:
            raise FileNotFoundError(f"No backup versions found for asset: {asset_id}")
        
        latest_backup = backup_versions[0]
        
        # Load backup metadata
        async with aiofiles.open(latest_backup / "backup_metadata.json", 'r') as f:
            backup_metadata = json.loads(await f.read())
        
        # Restore files
        restored_files = await self._restore_asset_files(latest_backup, asset_id)
        
        # Update asset registry
        self.asset_registry[asset_id] = backup_metadata["asset_metadata"]
        await self._save_asset_registry()
        
        return {
            "status": "success",
            "asset_id": asset_id,
            "restored_from": str(latest_backup),
            "restored_files": restored_files
        }

    async def create_backup(self, message: Message) -> Message:
        """Create a backup of specified assets."""
        asset_ids = message.content.get("asset_ids", [])
        backup_type = message.content.get("backup_type", "full")  # full, incremental
        
        try:
            backup_result = await self._create_asset_backup(asset_ids, backup_type)
            return Message(
                message_id=f"backup_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="backup_created",
                content={"backup_result": backup_result},
                context=message.context
            )
        except Exception as e:
            return Message(
                message_id=f"backup_{message.message_id}",
                sender=self.agent_id,
                receiver=message.sender,
                message_type="backup_failed",
                content={"error": str(e)},
                context=message.context
            )

    async def _create_asset_backup(self, asset_ids: List[str], backup_type: str) -> Dict[str, Any]:
        """Create backup of specified assets."""
        backup_results = []
        
        for asset_id in asset_ids:
            try:
                if asset_id not in self.asset_registry:
                    raise ValueError(f"Asset not found: {asset_id}")
                
                asset = self.asset_registry[asset_id]
                backup_path = self.asset_config["base_path"] / "backups" / asset_id / \
                             datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Create backup directory
                backup_path.mkdir(parents=True, exist_ok=True)
                
                # Copy asset files
                backed_up_files = await self._backup_asset_files(asset, backup_path, backup_type)
                
                # Save backup metadata
                backup_metadata = {
                    "asset_metadata": asset,
                    "backup_type": backup_type,
                    "backup_time": datetime.now().isoformat(),
                    "backed_up_files": backed_up_files
                }
                
                async with aiofiles.open(backup_path / "backup_metadata.json", 'w') as f:
                    await f.write(json.dumps(backup_metadata, indent=2))
                
                backup_results.append({
                    "asset_id": asset_id,
                    "status": "success",
                    "backup_path": str(backup_path),
                    "backup_type": backup_type
                })
                
            except Exception as e:
                backup_results.append({
                    "asset_id": asset_id,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "backup_results": backup_results,
            "backup_type": backup_type,
            "timestamp": datetime.now().isoformat()
        } 