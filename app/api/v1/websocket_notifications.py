"""
WebSocket endpoint for real-time notifications
No microservices needed - just add to existing FastAPI app
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
import json
import logging

from app.models.user import User
from app.api.v1.auth import get_current_user_ws

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections for real-time notifications"""
    
    def __init__(self):
        # Store active connections: {user_id: Set[WebSocket]}
        self.active_connections: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Connect a new WebSocket for a user"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        logger.info(f"✅ User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")
    
    def disconnect(self, websocket: WebSocket, user_id: int):
        """Disconnect a WebSocket"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            
            # Remove user entry if no more connections
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        logger.info(f"❌ User {user_id} disconnected")
    
    async def send_to_user(self, user_id: int, message: dict):
        """Send notification to all connections of a user"""
        if user_id not in self.active_connections:
            logger.info(f"⚠️  User {user_id} has no active connections")
            return
        
        # Send to all user's connections (multiple tabs/devices)
        disconnected = set()
        for websocket in self.active_connections[user_id]:
            try:
                await websocket.send_json(message)
                logger.info(f"📤 Sent notification to user {user_id}")
            except Exception as e:
                logger.error(f"❌ Failed to send to user {user_id}: {e}")
                disconnected.add(websocket)
        
        # Clean up failed connections
        for ws in disconnected:
            self.disconnect(ws, user_id)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected users"""
        for user_id in list(self.active_connections.keys()):
            await self.send_to_user(user_id, message)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/notifications")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = None  # JWT token passed as query param
):
    """
    WebSocket endpoint for real-time notifications
    
    Usage from frontend:
    const ws = new WebSocket(`wss://api.yourdomain.com/api/v1/ws/notifications?token=${accessToken}`)
    """
    
    # Authenticate user via token
    try:
        # Simple token validation (you'd use your JWT validation here)
        # For now, we'll require the token to be passed
        if not token:
            await websocket.close(code=1008, reason="Missing authentication token")
            return
        
        # TODO: Validate JWT token and get user_id
        # For now, placeholder - you'd decode JWT to get user_id
        from app.core.security import decode_access_token
        user_id = decode_access_token(token)  # Returns user_id
        
        if not user_id:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        await websocket.close(code=1008, reason="Authentication failed")
        return
    
    # Connect user
    await manager.connect(websocket, user_id)
    
    try:
        # Send initial connection success message
        await websocket.send_json({
            "type": "connection",
            "message": "Connected to notification service",
            "user_id": user_id
        })
        
        # Keep connection alive and listen for messages
        while True:
            # Wait for messages from client (like "ping" to keep alive)
            data = await websocket.receive_text()
            
            # Handle ping/pong for connection keep-alive
            if data == "ping":
                await websocket.send_json({"type": "pong"})
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        manager.disconnect(websocket, user_id)


# Helper function to send notifications via WebSocket
async def send_notification_to_user(user_id: int, notification: dict):
    """
    Send real-time notification to user
    Call this from your NotificationService.create_notification()
    """
    message = {
        "type": "notification",
        "data": notification
    }
    await manager.send_to_user(user_id, message)


# Helper function to broadcast system alerts
async def broadcast_system_alert(title: str, message: str):
    """
    Broadcast system-wide alert to all connected users
    """
    alert = {
        "type": "system_alert",
        "data": {
            "title": title,
            "message": message
        }
    }
    await manager.broadcast_to_all(alert)

