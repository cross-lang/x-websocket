"""
x-websocket 命令行入口点
"""
import asyncio
import sys
import logging
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .server import app
from .core.config import settings

console = Console()
logger = logging.getLogger(__name__)


@click.group()
@click.version_option()
def cli():
    """x-websocket - WebSocket-based LLM demonstration application"""
    pass


@cli.command()
@click.option("--host", default="0.0.0.0", help="服务器主机")
@click.option("--port", default=8765, help="服务器端口")
@click.option("--reload", is_flag=True, help="启用热重载")
def serve(host, port, reload):
    """启动WebSocket服务器"""
    import uvicorn

    console.print(Panel.fit(
        f"[bold green]x-websocket[/bold green] 服务器启动中...\n"
        f"主机: [cyan]{host}[/cyan]\n"
        f"端口: [cyan]{port}[/cyan]\n"
        f"热重载: [cyan]{'是' if reload else '否'}[/cyan]",
        title="服务器配置"
    ))

    uvicorn.run(
        "src.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


@cli.command()
def config():
    """显示当前配置"""
    table = Table(title="当前配置", show_header=True, header_style="bold magenta")
    table.add_column("配置项", style="dim", width=30)
    table.add_column("值", style="cyan")

    table.add_row("服务器主机", settings.host)
    table.add_row("服务器端口", str(settings.port))
    table.add_row("调试模式", str(settings.debug))
    table.add_row("LLM提供商", settings.llm_provider)
    table.add_row("OpenAI API密钥", settings.openai_api_key[:10] + "..." if settings.openai_api_key else "未设置")
    table.add_row("Kimi API密钥", settings.kimi_api_key[:10] + "..." if settings.kimi_api_key else "未设置")
    table.add_row("DeepSeek API密钥", settings.deepseek_api_key[:10] + "..." if settings.deepseek_api_key else "未设置")

    console.print(table)


@cli.command()
@click.argument("user_id")
def token(user_id):
    """生成JWT令牌"""
    from .auth.jwt_auth import JWTAuthService

    auth_service = JWTAuthService(
        secret_key=settings.jwt_secret,
        algorithm=settings.jwt_algorithm
    )

    token = auth_service.create_token(user_id)
    console.print(Panel(
        f"[bold green]用户ID:[/bold green] {user_id}\n"
        f"[bold green]令牌:[/bold green] {token}",
        title="JWT令牌",
        border_style="green"
    ))


@cli.command()
def health():
    """检查服务器健康状态"""
    import httpx

    url = f"http://{settings.host}:{settings.port}/health"
    try:
        response = httpx.get(url, timeout=5)
        if response.status_code == 200:
            console.print("[green]✓[/green] 服务器健康")
        else:
            console.print(f"[red]✗[/red] 服务器异常: {response.status_code}")
    except Exception as e:
        console.print(f"[red]✗[/red] 无法连接到服务器: {e}")


def main():
    """主函数"""
    cli()


if __name__ == "__main__":
    main()