import json
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[int, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        connection_id = f"{user_id}_{datetime.now().timestamp()}"
        self.active_connections[connection_id] = websocket
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        return connection_id

    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            del self.active_connections[connection_id]
            
            # Retirer de user_connections
            for user_id, connections in self.user_connections.items():
                if connection_id in connections:
                    connections.remove(connection_id)
                    if not connections:
                        del self.user_connections[user_id]
                    break

    async def send_personal_message(self, message: str, user_id: int):
        """Envoyer un message à un utilisateur spécifique"""
        if user_id in self.user_connections:
            disconnected = []
            for connection_id in self.user_connections[user_id]:
                try:
                    websocket = self.active_connections[connection_id]
                    await websocket.send_text(message)
                except:
                    disconnected.append(connection_id)
            
            # Nettoyer les connexions fermées
            for conn_id in disconnected:
                self.disconnect(conn_id)

    async def broadcast(self, message: str):
        """Diffuser un message à tous les utilisateurs connectés"""
        disconnected = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except:
                disconnected.append(connection_id)
        
        # Nettoyer les connexions fermées
        for conn_id in disconnected:
            self.disconnect(conn_id)

    async def notify_dossier_update(self, user_id: int, dossier_data: dict):
        """Notifier un utilisateur d'une mise à jour de dossier"""
        notification = {
            "type": "dossier_update",
            "data": dossier_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.send_personal_message(json.dumps(notification), user_id)

    async def notify_new_alert(self, user_id: int, alert_data: dict):
        """Notifier un utilisateur d'une nouvelle alerte"""
        notification = {
            "type": "new_alert",
            "data": alert_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.send_personal_message(json.dumps(notification), user_id)

    async def notify_deadline_reminder(self, user_id: int, reminder_data: dict):
        """Notifier un utilisateur d'un rappel d'échéance"""
        notification = {
            "type": "deadline_reminder",
            "data": reminder_data,
            "timestamp": datetime.now().isoformat()
        }
        await self.send_personal_message(json.dumps(notification), user_id)


manager = ConnectionManager()