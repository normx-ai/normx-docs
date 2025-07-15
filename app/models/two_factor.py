"""
Modèle pour l'authentification à deux facteurs
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import pyotp
import qrcode
import io
import base64

from app.core.database import Base


class TwoFactorAuth(Base):
    """Gestion de l'authentification à deux facteurs"""
    __tablename__ = "two_factor_auth"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Secret pour TOTP (Time-based One-Time Password)
    secret = Column(String, nullable=False)
    
    # Codes de récupération (backup codes)
    backup_codes = Column(String)  # JSON stockant les codes hashés
    
    # État de l'activation
    enabled = Column(Boolean, default=False)
    activated_at = Column(DateTime(timezone=True))
    
    # Métadonnées
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relations
    user = relationship("User", backref="two_factor_auth", uselist=False)
    
    def generate_secret(self) -> str:
        """Génère un nouveau secret pour 2FA"""
        self.secret = pyotp.random_base32()
        return self.secret
    
    def get_totp_uri(self, email: str, issuer: str = "NormX Docs") -> str:
        """Génère l'URI pour QR code"""
        return pyotp.totp.TOTP(self.secret).provisioning_uri(
            name=email,
            issuer_name=issuer
        )
    
    def generate_qr_code(self, email: str) -> str:
        """Génère un QR code en base64"""
        uri = self.get_totp_uri(email)
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        
        return base64.b64encode(buf.getvalue()).decode()
    
    def verify_token(self, token: str) -> bool:
        """Vérifie un token TOTP"""
        totp = pyotp.TOTP(self.secret)
        return totp.verify(token, valid_window=1)
    
    def generate_backup_codes(self, count: int = 8) -> list[str]:
        """Génère des codes de récupération"""
        import secrets
        import json
        from passlib.hash import pbkdf2_sha256
        
        codes = []
        hashed_codes = []
        
        for _ in range(count):
            code = f"{secrets.randbelow(1000000):06d}"
            codes.append(code)
            hashed_codes.append(pbkdf2_sha256.hash(code))
        
        self.backup_codes = json.dumps(hashed_codes)
        return codes
    
    def verify_backup_code(self, code: str) -> bool:
        """Vérifie et consomme un code de récupération"""
        import json
        from passlib.hash import pbkdf2_sha256
        
        if not self.backup_codes:
            return False
        
        hashed_codes = json.loads(self.backup_codes)
        
        for i, hashed_code in enumerate(hashed_codes):
            if pbkdf2_sha256.verify(code, hashed_code):
                # Supprimer le code utilisé
                hashed_codes.pop(i)
                self.backup_codes = json.dumps(hashed_codes)
                return True
        
        return False