"""
Serviço de Segurança - CAPTCHA e Bloqueio de IP
"""
import os
import random
import string
import hashlib
import time
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from flask import request, session
from database import db
from models.models import BlockedIP, LoginAttempt, UserActivity

class SecurityService:
    def __init__(self):
        self.max_attempts = 8
        self.block_duration_hours = 24
    
    def generate_captcha(self):
        """Gera um CAPTCHA simples e legível"""
        # Criar imagem maior para melhor legibilidade
        width, height = 200, 80
        image = Image.new('RGB', (width, height), color='#f8f9fa')
        draw = ImageDraw.Draw(image)
        
        # Gerar texto aleatório (apenas números para facilitar)
        captcha_text = ''.join(random.choices(string.digits, k=4))
        
        # Salvar na sessão
        session['captcha_text'] = captcha_text
        
        try:
            # Tentar usar uma fonte do sistema maior
            font = ImageFont.truetype("arial.ttf", 32)
        except:
            try:
                # Tentar outras fontes comuns
                font = ImageFont.truetype("calibri.ttf", 32)
            except:
                # Fallback para fonte padrão maior
                font = ImageFont.load_default()
        
        # Desenhar fundo com cor suave
        draw.rectangle([0, 0, width, height], fill='#f8f9fa')
        
        # Desenhar texto centralizado e legível
        text_bbox = draw.textbbox((0, 0), captcha_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2 - 5
        
        # Desenhar texto com sombra para melhor legibilidade
        draw.text((x + 2, y + 2), captcha_text, fill='#6c757d', font=font)
        draw.text((x, y), captcha_text, fill='#212529', font=font)
        
        # Adicionar borda sutil
        draw.rectangle([0, 0, width-1, height-1], outline='#dee2e6', width=2)
        
        # Adicionar apenas algumas linhas sutis de ruído
        for _ in range(3):
            x1 = random.randint(10, width-10)
            y1 = random.randint(10, height-10)
            x2 = random.randint(10, width-10)
            y2 = random.randint(10, height-10)
            draw.line([(x1, y1), (x2, y2)], fill='#e9ecef', width=1)
        
        # Converter para base64
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{image_base64}"
    
    def verify_captcha(self, user_input):
        """Verifica se o CAPTCHA está correto"""
        if 'captcha_text' not in session:
            return False
        
        correct_text = session.get('captcha_text', '').lower()
        user_text = user_input.lower().strip()
        
        # Limpar o CAPTCHA da sessão após verificação
        session.pop('captcha_text', None)
        
        return correct_text == user_text
    
    def get_client_ip(self):
        """Obtém o IP real do cliente"""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr
    
    def is_ip_blocked(self, ip_address):
        """Verifica se o IP está bloqueado"""
        blocked_ip = BlockedIP.query.filter_by(
            ip_address=ip_address,
            is_active=True
        ).first()
        
        if not blocked_ip:
            return False
        
        # Verificar se o bloqueio ainda é válido
        if blocked_ip.blocked_at:
            block_duration = timedelta(hours=self.block_duration_hours)
            if datetime.utcnow() - blocked_ip.blocked_at > block_duration:
                # Bloqueio expirado, desativar
                blocked_ip.is_active = False
                db.session.commit()
                return False
        
        return True
    
    def record_login_attempt(self, ip_address, username, success, user_agent=None):
        """Registra uma tentativa de login"""
        attempt = LoginAttempt(
            ip_address=ip_address,
            username=username,
            success=success,
            user_agent=user_agent or request.headers.get('User-Agent', 'N/A')
        )
        db.session.add(attempt)
        db.session.commit()
        
        return attempt
    
    def get_failed_attempts_count(self, ip_address, hours=24):
        """Conta tentativas falhadas nas últimas X horas"""
        since_time = datetime.utcnow() - timedelta(hours=hours)
        
        count = LoginAttempt.query.filter(
            LoginAttempt.ip_address == ip_address,
            LoginAttempt.success == False,
            LoginAttempt.created_at >= since_time
        ).count()
        
        return count
    
    def block_ip(self, ip_address, reason="Múltiplas tentativas de login falhadas", blocked_by=None):
        """Bloqueia um IP"""
        # Verificar se já está bloqueado
        existing_block = BlockedIP.query.filter_by(ip_address=ip_address).first()
        
        if existing_block:
            if existing_block.is_active:
                return existing_block  # Já está bloqueado
            
            # Reativar bloqueio existente
            existing_block.is_active = True
            existing_block.blocked_at = datetime.utcnow()
            existing_block.reason = reason
            existing_block.blocked_by = blocked_by
            existing_block.unblocked_at = None
            existing_block.unblocked_by = None
            db.session.commit()
            return existing_block
        
        # Criar novo bloqueio
        failed_attempts = self.get_failed_attempts_count(ip_address)
        
        blocked_ip = BlockedIP(
            ip_address=ip_address,
            reason=reason,
            failed_attempts=failed_attempts,
            blocked_by=blocked_by
        )
        
        db.session.add(blocked_ip)
        db.session.commit()
        
        return blocked_ip
    
    def unblock_ip(self, ip_address, unblocked_by=None):
        """Desbloqueia um IP"""
        blocked_ip = BlockedIP.query.filter_by(
            ip_address=ip_address,
            is_active=True
        ).first()
        
        if blocked_ip:
            blocked_ip.is_active = False
            blocked_ip.unblocked_at = datetime.utcnow()
            blocked_ip.unblocked_by = unblocked_by
            db.session.commit()
            
            return True
        
        return False
    
    def check_and_handle_failed_login(self, ip_address, username):
        """Verifica e trata tentativas de login falhadas"""
        # Registrar tentativa falhada
        self.record_login_attempt(ip_address, username, False)
        
        # Contar tentativas falhadas
        failed_count = self.get_failed_attempts_count(ip_address)
        
        # Se excedeu o limite, bloquear IP
        if failed_count >= self.max_attempts:
            self.block_ip(ip_address, f"Múltiplas tentativas de login falhadas ({failed_count} tentativas)")
            
            # Registrar atividade de bloqueio
            activity = UserActivity(
                user_id=None,  # Sistema
                action='ip_blocked',
                details=f'IP {ip_address} bloqueado por {failed_count} tentativas falhadas',
                ip_address=ip_address
            )
            db.session.add(activity)
            db.session.commit()
            
            return True  # IP foi bloqueado
        
        return False  # IP não foi bloqueado
    
    def get_blocked_ips(self):
        """Retorna lista de IPs bloqueados"""
        return BlockedIP.query.filter_by(is_active=True).order_by(BlockedIP.blocked_at.desc()).all()
    
    def get_all_blocked_ips(self):
        """Retorna todos os IPs bloqueados (ativos e inativos)"""
        return BlockedIP.query.order_by(BlockedIP.blocked_at.desc()).all()

# Instância global do serviço
security_service = SecurityService()
