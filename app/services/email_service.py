"""
Service pour l'envoi d'emails
"""

import os
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        # Configuration SMTP
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_from_email = settings.SMTP_FROM_EMAIL
        self.smtp_from_name = settings.SMTP_FROM_NAME
        self.smtp_tls = getattr(settings, 'SMTP_TLS', True)
        self.smtp_ssl = getattr(settings, 'SMTP_SSL', False)
        
        # Créer le répertoire des templates s'il n'existe pas
        template_dir = Path(getattr(settings, 'EMAIL_TEMPLATES_DIR', 'templates/email'))
        template_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration Jinja2 pour les templates
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        template_data: Dict[str, Any],
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Envoie un email en utilisant un template
        
        Args:
            to_email: Email du destinataire
            subject: Sujet de l'email
            template_name: Nom du template (sans extension)
            template_data: Données pour le template
            cc: Liste des emails en copie
            bcc: Liste des emails en copie cachée
            attachments: Liste des pièces jointes
            
        Returns:
            bool: True si l'envoi a réussi
        """
        try:
            # Charger les templates HTML et texte
            html_template = self._get_template(f"{template_name}.html")
            text_template = self._get_template(f"{template_name}.txt")
            
            # Rendre les templates avec les données
            html_content = html_template.render(**template_data) if html_template else None
            text_content = text_template.render(**template_data) if text_template else None
            
            # Créer le message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{self.smtp_from_name} <{self.smtp_from_email}>"
            message['To'] = to_email
            
            if cc:
                message['Cc'] = ', '.join(cc)
            
            # Ajouter le contenu texte et HTML
            if text_content:
                message.attach(MIMEText(text_content, 'plain', 'utf-8'))
            if html_content:
                message.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # Ajouter les pièces jointes si présentes
            if attachments:
                for attachment in attachments:
                    # TODO: Implémenter l'ajout de pièces jointes
                    pass
            
            # Préparer la liste des destinataires
            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)
            
            # Envoyer l'email
            await self._send_smtp(message, recipients)
            
            logger.info(f"Email envoyé avec succès à {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email à {to_email}: {str(e)}")
            return False
    
    async def send_welcome_email(self, to_email: str, user_name: str, cabinet_name: str) -> bool:
        """
        Envoie un email de bienvenue après inscription
        """
        return await self.send_email(
            to_email=to_email,
            subject=f"Bienvenue dans {cabinet_name} !",
            template_name="welcome",
            template_data={
                "user_name": user_name,
                "cabinet_name": cabinet_name,
                "login_url": "http://localhost:3000/login",
                "support_email": self.smtp_from_email
            }
        )
    
    async def send_notification_echeance(
        self,
        to_email: str,
        user_name: str,
        dossier_reference: str,
        client_name: str,
        echeance_date: str,
        days_remaining: int
    ) -> bool:
        """Envoie une notification d'échéance proche"""
        template_data = {
            "user_name": user_name,
            "dossier_reference": dossier_reference,
            "client_name": client_name,
            "echeance_date": echeance_date,
            "days_remaining": days_remaining,
            "app_url": "http://localhost:3000"  # TODO: Configurer l'URL de l'app
        }
        
        subject = f"Échéance proche - {client_name} ({dossier_reference})"
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            template_name="echeance_proche",
            template_data=template_data
        )
    
    async def send_document_manquant(
        self,
        to_email: str,
        user_name: str,
        dossier_reference: str,
        client_name: str,
        documents_manquants: List[str],
        mois: str,
        annee: int
    ) -> bool:
        """Envoie une notification de documents manquants"""
        template_data = {
            "user_name": user_name,
            "dossier_reference": dossier_reference,
            "client_name": client_name,
            "documents_manquants": documents_manquants,
            "periode": f"{mois} {annee}",
            "app_url": "http://localhost:3000"
        }
        
        subject = f"Documents manquants - {client_name} ({mois} {annee})"
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            template_name="documents_manquants",
            template_data=template_data
        )
    
    async def send_tache_retard(
        self,
        to_email: str,
        user_name: str,
        dossier_reference: str,
        client_name: str,
        taches_retard: List[Dict[str, Any]]
    ) -> bool:
        """Envoie une notification de tâches en retard"""
        template_data = {
            "user_name": user_name,
            "dossier_reference": dossier_reference,
            "client_name": client_name,
            "taches_retard": taches_retard,
            "app_url": "http://localhost:3000"
        }
        
        subject = f"Tâches en retard - {client_name}"
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            template_name="taches_retard",
            template_data=template_data
        )
    
    async def send_welcome_email(
        self,
        to_email: str,
        user_name: str,
        username: str,
        temporary_password: str
    ) -> bool:
        """Envoie un email de bienvenue avec les identifiants"""
        template_data = {
            "user_name": user_name,
            "username": username,
            "temporary_password": temporary_password,
            "app_url": "http://localhost:3000"
        }
        
        subject = "Bienvenue sur la plateforme Cabinet Comptable"
        
        return await self.send_email(
            to_email=to_email,
            subject=subject,
            template_name="welcome",
            template_data=template_data
        )
    
    def _get_template(self, template_path: str):
        """Récupère un template s'il existe"""
        try:
            return self.jinja_env.get_template(template_path)
        except:
            return None
    
    async def _send_smtp(self, message: MIMEMultipart, recipients: List[str]):
        """Envoie le message via SMTP"""
        if not self.smtp_user or not self.smtp_password:
            logger.warning("Configuration SMTP incomplète, email non envoyé")
            return
        
        # Connexion SMTP
        if self.smtp_ssl:
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=True
            )
        else:
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=self.smtp_tls
            )


# Instance singleton du service
email_service = EmailService()