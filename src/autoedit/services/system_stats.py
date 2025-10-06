"""System statistics helpers for rendering runtime telemetry in the UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import re
import subprocess


@dataclass
class CudaStatus:
    """Represents the CUDA availability on the current host."""

    available: bool
    detail: str = ""


@dataclass
class MemoryUsage:
    """Represents a memory usage snapshot."""

    used_bytes: Optional[int]
    total_bytes: Optional[int]

    @property
    def percent(self) -> Optional[float]:
        if self.used_bytes is None or self.total_bytes in (None, 0):
            return None
        return (self.used_bytes / self.total_bytes) * 100


def _parse_meminfo() -> Optional[MemoryUsage]:
    """Parse `/proc/meminfo` for total and available system memory."""

    try:
        with open("/proc/meminfo", "r", encoding="utf-8") as meminfo:
            content = meminfo.read()
    except OSError:
        return None

    total_match = re.search(r"MemTotal:\s+(\d+)\s+kB", content)
    available_match = re.search(r"MemAvailable:\s+(\d+)\s+kB", content)

    if not total_match or not available_match:
        return None

    total_kb = int(total_match.group(1))
    available_kb = int(available_match.group(1))
    used_kb = total_kb - available_kb

    return MemoryUsage(used_bytes=used_kb * 1024, total_bytes=total_kb * 1024)


def get_ram_usage() -> MemoryUsage:
    """Return the current system RAM usage."""

    try:
        import psutil  # type: ignore
    except ModuleNotFoundError:
        parsed = _parse_meminfo()
        return parsed or MemoryUsage(used_bytes=None, total_bytes=None)

    try:
        virtual_memory = psutil.virtual_memory()
    except Exception:
        parsed = _parse_meminfo()
        return parsed or MemoryUsage(used_bytes=None, total_bytes=None)

    used = virtual_memory.total - virtual_memory.available
    return MemoryUsage(used_bytes=int(used), total_bytes=int(virtual_memory.total))


def get_cuda_status() -> CudaStatus:
    """Check whether CUDA is available via PyTorch or NVIDIA tooling."""

    try:
        import torch  # type: ignore
    except ModuleNotFoundError:
        return CudaStatus(False, "PyTorch not installed")
    except Exception as exc:  # pragma: no cover - defensive guard
        return CudaStatus(False, f"PyTorch error: {exc}")

    try:
        if not torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            if device_count:
                return CudaStatus(False, "Driver initialisation failed")
            return CudaStatus(False, "No CUDA device detected")

        device_index = torch.cuda.current_device()
        device_name = torch.cuda.get_device_name(device_index)
        return CudaStatus(True, device_name)
    except Exception as exc:  # pragma: no cover - defensive guard
        return CudaStatus(False, f"CUDA check failed: {exc}")


def _query_nvidia_smi() -> Optional[MemoryUsage]:
    """Attempt to read GPU memory statistics via the NVIDIA CLI utility."""

    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None

    output = result.stdout.strip().splitlines()
    if not output:
        return None

    first_line = output[0]
    parts = [segment.strip() for segment in first_line.split(",") if segment.strip()]
    if len(parts) < 2:
        return None

    try:
        used_mb = float(parts[0])
        total_mb = float(parts[1])
    except ValueError:
        return None

    used_bytes = int(used_mb * 1024 * 1024)
    total_bytes = int(total_mb * 1024 * 1024)
    return MemoryUsage(used_bytes=used_bytes, total_bytes=total_bytes)


def get_vram_usage() -> MemoryUsage:
    """Return the VRAM usage for the primary CUDA device if available."""

    try:
        import torch  # type: ignore
    except ModuleNotFoundError:
        torch = None  # type: ignore
    except Exception:
        torch = None  # type: ignore

    if torch is not None:
        try:
            if torch.cuda.is_available():
                device_index = torch.cuda.current_device()
                free_bytes, total_bytes = torch.cuda.mem_get_info(device_index)
                used_bytes = total_bytes - free_bytes
                return MemoryUsage(used_bytes=int(used_bytes), total_bytes=int(total_bytes))
        except Exception:
            pass

    smi_result = _query_nvidia_smi()
    if smi_result:
        return smi_result

    return MemoryUsage(used_bytes=None, total_bytes=None)


def format_bytes_to_gb(value: Optional[int]) -> str:
    """Format a byte count as a human readable string in gigabytes."""

    if value is None:
        return "—"

    gb_value = value / (1024 ** 3)
    return f"{gb_value:.1f} GB"
