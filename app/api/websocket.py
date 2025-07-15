from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
import json

from app.core.database import get_db
from app.core.websocket import manager
from app.api.auth import get_current_user_websocket

router = APIRouter()


@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    Endpoint WebSocket pour les notifications en temps réel
    Le token JWT doit être passé dans l'URL
    """
    try:
        # Authentifier l'utilisateur via le token
        user = await get_current_user_websocket(token)
        if not user:
            await websocket.close(code=4001, reason="Unauthorized")
            return
            
        # Connecter l'utilisateur
        connection_id = await manager.connect(websocket, user.id)
        
        # Envoyer un message de bienvenue
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": f"Bienvenue {user.full_name}! Vous êtes maintenant connecté aux notifications.",
            "user_id": user.id
        }))
        
        try:
            while True:
                # Attendre les messages du client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Traiter différents types de messages
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": message.get("timestamp")
                    }))
                elif message.get("type") == "subscribe":
                    # Permettre de s'abonner à des types spécifiques de notifications
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "channel": message.get("channel", "all")
                    }))
                    
        except WebSocketDisconnect:
            manager.disconnect(connection_id)
            
    except Exception as e:
        await websocket.close(code=4002, reason=str(e))