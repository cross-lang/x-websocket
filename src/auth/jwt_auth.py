"""
JWT认证服务
"""
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class JWTAuthService:
    """JWT认证服务"""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """
        创建JWT令牌

        Args:
            user_id: 用户ID
            expires_delta: 过期时间间隔，默认为15分钟

        Returns:
            JWT令牌字符串
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=15)

        expire = datetime.utcnow() + expires_delta

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.debug(f"为用户 {user_id} 创建令牌，过期时间: {expire}")
        return token

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        验证JWT令牌

        Args:
            token: JWT令牌

        Returns:
            解码后的令牌负载

        Raises:
            jwt.PyJWTError: 令牌无效或过期
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("令牌已过期")
            raise
        except jwt.InvalidTokenError as e:
            logger.warning(f"无效令牌: {e}")
            raise

    def create_refresh_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """
        创建刷新令牌

        Args:
            user_id: 用户ID
            expires_delta: 过期时间间隔，默认为7天

        Returns:
            刷新令牌字符串
        """
        if expires_delta is None:
            expires_delta = timedelta(days=7)

        expire = datetime.utcnow() + expires_delta

        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.debug(f"为用户 {user_id} 创建刷新令牌，过期时间: {expire}")
        return token

    def refresh_access_token(self, refresh_token: str) -> str:
        """
        使用刷新令牌获取新的访问令牌

        Args:
            refresh_token: 刷新令牌

        Returns:
            新的访问令牌

        Raises:
            jwt.PyJWTError: 刷新令牌无效
        """
        try:
            payload = self.verify_token(refresh_token)
            if payload.get("type") != "refresh":
                raise jwt.InvalidTokenError("令牌类型不是刷新令牌")

            user_id = payload.get("sub")
            if not user_id:
                raise jwt.InvalidTokenError("无效的令牌负载")

            return self.create_token(user_id)
        except jwt.PyJWTError as e:
            logger.error(f"刷新令牌失败: {e}")
            raise