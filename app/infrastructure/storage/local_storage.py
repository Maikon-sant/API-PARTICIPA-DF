"""
Storage local de arquivos.
Salva em uploads/{manifestation_id}/{attachment_id}.{ext}
Compatível com draft (sem protocolo) e manifestações finalizadas.
Nunca expõe caminhos internos; acesso via API.
"""

from pathlib import Path

from app.core.config import get_settings


class LocalStorage:
    """Armazena e recupera arquivos no disco local."""

    def __init__(self) -> None:
        base = get_settings().uploads_dir
        self._base = base.resolve() if isinstance(base, Path) else Path(base).resolve()

    def _manifestation_dir(self, manifestation_id: str) -> Path:
        """Diretório da manifestação: uploads/{manifestation_id}/."""
        d = self._base / manifestation_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save(
        self,
        manifestation_id: str,
        attachment_id: str,
        content: bytes,
        extension: str,
    ) -> str:
        """
        Salva arquivo e retorna path relativo (para persistir no banco).
        Formato: {manifestation_id}/{attachment_id}.{ext}
        Garante que o arquivo foi escrito no disco antes de retornar.
        """
        directory = self._manifestation_dir(manifestation_id)
        ext = extension.lstrip(".")
        filename = f"{attachment_id}.{ext}"
        path = directory / filename
        
        with path.open("wb") as f:
            f.write(content)
            f.flush()
            import os
            try:
                os.fsync(f.fileno())
            except (OSError, AttributeError):
                pass
        
        if not path.exists():
            raise RuntimeError(f"Arquivo não foi salvo: {path}")
        
        if path.stat().st_size != len(content):
            raise RuntimeError(f"Arquivo salvo com tamanho incorreto: esperado {len(content)}, obtido {path.stat().st_size}")
        
        return f"{manifestation_id}/{filename}"

    def full_path(self, relative_path: str) -> Path:
        """Path absoluto do arquivo a partir do path relativo armazenado."""
        return self._base / relative_path

    def exists(self, relative_path: str) -> bool:
        """Verifica se o arquivo existe."""
        return self.full_path(relative_path).exists()

    def read_bytes(self, relative_path: str) -> bytes:
        """Lê conteúdo do arquivo."""
        return self.full_path(relative_path).read_bytes()
