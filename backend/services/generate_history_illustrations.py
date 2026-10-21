"""
Offline Local Illustration Manager & Feasibility Checker for History Learning Hub.

Hardware Constraints Assessed:
- System RAM: ~8 GB (Observed Free: ~0.71 GB)
- GPU VRAM: 4 GB (NVIDIA GeForce RTX 2050)
- Available Disk Space: ~1.30 GB Free

Safety & Stability Rules:
1. Never attempt to download 2.5GB+ checkpoints (SD-Turbo or SD 1.5) when disk space is < 4 GB.
2. Never load heavy diffusion pipelines alongside Ollama and ChromaDB in constrained RAM.
3. Generate and maintain curated local visual storytelling assets in `frontend/public/illustrations/history/`.
4. Output a manifest (`manifest.json`) linking each lesson to its visual asset.
"""
from __future__ import annotations

import os
import sys
import json
import shutil
import psutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ILLUSTRATIONS_DIR = PROJECT_ROOT / "frontend" / "public" / "illustrations" / "history"
MANIFEST_PATH = ILLUSTRATIONS_DIR / "manifest.json"


def check_hardware_feasibility() -> dict:
    """Inspect actual RAM, VRAM, and disk space to evaluate model download safety."""
    mem = psutil.virtual_memory()
    disk = shutil.disk_usage(str(PROJECT_ROOT))

    free_ram_gb = round(mem.available / (1024**3), 2)
    total_ram_gb = round(mem.total / (1024**3), 2)
    free_disk_gb = round(disk.free / (1024**3), 2)

    has_enough_disk = free_disk_gb >= 4.0
    has_enough_ram = free_ram_gb >= 3.0

    return {
        "total_ram_gb": total_ram_gb,
        "free_ram_gb": free_ram_gb,
        "free_disk_gb": free_disk_gb,
        "has_enough_disk_for_weights": has_enough_disk,
        "has_enough_ram_for_diffusion": has_enough_ram,
        "feasible_for_sd": (has_enough_disk and has_enough_ram),
        "recommendation": "Use curated local vector illustrations" if not (has_enough_disk and has_enough_ram) else "SD model feasible"
    }


# High quality curated SVG illustrations for key historical lessons
CURATED_ASSETS = {
    "saints_pandharpur": {
        "lesson_id": "HIST_L02",
        "lesson_title": "Work of the Saints",
        "filename": "saints_pandharpur.svg",
        "title": "Pilgrimage to Pandharpur & The Saints",
        "caption": "Devotees uniting at Pandharpur in love and equality",
        "svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" width="100%" height="100%">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#FEF3C7"/>
      <stop offset="60%" stop-color="#FDE68A"/>
      <stop offset="100%" stop-color="#F59E0B"/>
    </linearGradient>
    <linearGradient id="temple" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#B45309"/>
      <stop offset="100%" stop-color="#78350F"/>
    </linearGradient>
    <linearGradient id="flag" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#EA580C"/>
      <stop offset="100%" stop-color="#F97316"/>
    </linearGradient>
  </defs>
  <rect width="600" height="400" fill="url(#sky)"/>
  <!-- Sun -->
  <circle cx="300" cy="140" r="50" fill="#FBBF24" opacity="0.6"/>
  <!-- Distant Chandrabhaga River -->
  <path d="M0 290 Q150 260 300 280 T600 270 L600 400 L0 400 Z" fill="#D97706" opacity="0.25"/>
  <path d="M0 320 Q200 300 400 330 T600 310 L600 400 L0 400 Z" fill="#B45309" opacity="0.3"/>
  <!-- Pandharpur Temple Spire (Shikhara) -->
  <polygon points="300,50 275,180 325,180" fill="url(#temple)"/>
  <rect x="270" y="180" width="60" height="70" fill="url(#temple)"/>
  <!-- Kalash and Saffron Flag (Bhagwa Zenda) -->
  <line x1="300" y1="50" x2="300" y2="20" stroke="#78350F" stroke-width="3"/>
  <path d="M300 20 L350 32 L300 45 Z" fill="url(#flag)"/>
  <circle cx="300" cy="50" r="6" fill="#FCD34D"/>
  <!-- Devotees Gathering -->
  <circle cx="210" cy="330" r="14" fill="#92400E"/>
  <path d="M195 344 C195 330 225 330 225 344 L220 380 L200 380 Z" fill="#D97706"/>
  <circle cx="250" cy="325" r="13" fill="#78350F"/>
  <path d="M236 338 C236 325 264 325 264 338 L260 380 L240 380 Z" fill="#B45309"/>
  <circle cx="350" cy="328" r="13" fill="#92400E"/>
  <path d="M336 341 C336 328 364 328 364 341 L360 380 L340 380 Z" fill="#EA580C"/>
  <circle cx="390" cy="335" r="14" fill="#78350F"/>
  <path d="M375 349 C375 335 405 335 405 349 L400 385 L380 385 Z" fill="#D97706"/>
  <!-- Tulsi Vrindavan / Veena -->
  <rect x="290" y="320" width="20" height="25" fill="#78350F"/>
  <!-- Caption Box -->
  <rect x="20" y="20" width="260" height="52" rx="8" fill="#FFFDF9" opacity="0.9" stroke="#E5DBCA"/>
  <text x="32" y="42" font-family="Inter, sans-serif" font-size="14" font-weight="bold" fill="#78350F">Work of the Saints</text>
  <text x="32" y="60" font-family="Inter, sans-serif" font-size="11" fill="#92400E">Devotion, Equality &amp; Compassion</text>
</svg>"""
    },
    "shivneri_fort": {
        "lesson_id": "HIST_L04",
        "lesson_title": "Shivaji's Childhood",
        "filename": "shivneri_fort.svg",
        "title": "Fort Shivneri near Junnar",
        "caption": "The historic birthplace of Chhatrapati Shivaji Maharaj",
        "svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" width="100%" height="100%">
  <defs>
    <linearGradient id="sky2" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#FEF9C3"/>
      <stop offset="100%" stop-color="#FBBF24"/>
    </linearGradient>
    <linearGradient id="mountain" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#78350F"/>
      <stop offset="100%" stop-color="#451A03"/>
    </linearGradient>
  </defs>
  <rect width="600" height="400" fill="url(#sky2)"/>
  <!-- Mountain Silhouette of Shivneri -->
  <polygon points="80,400 240,140 360,140 520,400" fill="url(#mountain)"/>
  <!-- Fort Bastions (Buruj) -->
  <rect x="235" y="130" width="30" height="30" fill="#92400E" rx="2"/>
  <rect x="335" y="130" width="30" height="30" fill="#92400E" rx="2"/>
  <rect x="260" y="140" width="80" height="20" fill="#78350F"/>
  <!-- Fort Entrance Arch (Maha Darwaza) -->
  <path d="M285 160 Q300 145 315 160 L315 160 L285 160 Z" fill="#451A03"/>
  <!-- Saffron Flag fluttering -->
  <line x1="300" y1="130" x2="300" y2="90" stroke="#F59E0B" stroke-width="3"/>
  <path d="M300 90 L350 102 L300 115 Z" fill="#EA580C"/>
  <!-- Title Badge -->
  <rect x="20" y="20" width="220" height="52" rx="8" fill="#FFFDF9" opacity="0.9" stroke="#E5DBCA"/>
  <text x="32" y="42" font-family="Inter, sans-serif" font-size="14" font-weight="bold" fill="#78350F">Fort Shivneri</text>
  <text x="32" y="60" font-family="Inter, sans-serif" font-size="11" fill="#92400E">Birthplace of Swaraj · 1630</text>
</svg>"""
    },
    "pratapgad_fort": {
        "lesson_id": "HIST_L09",
        "lesson_title": "Pratapgad makes History",
        "filename": "pratapgad_fort.svg",
        "title": "Fort Pratapgad & The Sahyadri Hills",
        "caption": "The mountain stronghold where Afzalkhan was defeated",
        "svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" width="100%" height="100%">
  <defs>
    <linearGradient id="sky3" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#FEF3C7"/>
      <stop offset="100%" stop-color="#F59E0B"/>
    </linearGradient>
    <linearGradient id="cliff" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#57534E"/>
      <stop offset="100%" stop-color="#1C1917"/>
    </linearGradient>
  </defs>
  <rect width="600" height="400" fill="url(#sky3)"/>
  <!-- Dense Javali Forest Hills -->
  <polygon points="0,400 150,220 300,400" fill="#14532D" opacity="0.8"/>
  <polygon points="300,400 450,230 600,400" fill="#14532D" opacity="0.7"/>
  <!-- Steep Bhorpya Hill & Fort Pratapgad -->
  <polygon points="180,400 300,110 420,400" fill="url(#cliff)"/>
  <!-- Fort Bastions (Buruj) atop hill -->
  <rect x="270" y="100" width="60" height="25" fill="#44403C" rx="3"/>
  <circle cx="280" cy="100" r="10" fill="#292524"/>
  <circle cx="320" cy="100" r="10" fill="#292524"/>
  <!-- Saffron Flag -->
  <line x1="300" y1="100" x2="300" y2="60" stroke="#F59E0B" stroke-width="3"/>
  <path d="M300 60 L350 72 L300 85 Z" fill="#EA580C"/>
  <!-- Meeting Shamiana Tent at foot of fort -->
  <polygon points="120,360 160,310 200,360" fill="#BE185D"/>
  <polygon points="160,310 150,295 170,295" fill="#FCD34D"/>
  <!-- Title Badge -->
  <rect x="20" y="20" width="240" height="52" rx="8" fill="#FFFDF9" opacity="0.9" stroke="#E5DBCA"/>
  <text x="32" y="42" font-family="Inter, sans-serif" font-size="14" font-weight="bold" fill="#78350F">Fort Pratapgad</text>
  <text x="32" y="60" font-family="Inter, sans-serif" font-size="11" fill="#92400E">Historic Encounter · 1659</text>
</svg>"""
    },
    "sindhudurg_fort": {
        "lesson_id": "HIST_L17",
        "lesson_title": "Management of Forts and the Navy",
        "filename": "sindhudurg_fort.svg",
        "title": "Sea Fort of Sindhudurg (Malvan)",
        "caption": "Shivaji Maharaj's invincible naval bastion in the Arabian Sea",
        "svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400" width="100%" height="100%">
  <defs>
    <linearGradient id="sea" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0284C7"/>
      <stop offset="100%" stop-color="#0369A1"/>
    </linearGradient>
  </defs>
  <!-- Sky -->
  <rect width="600" height="240" fill="#FEF3C7"/>
  <!-- Sea -->
  <rect y="240" width="600" height="160" fill="url(#sea)"/>
  <!-- Kurte Island Fort Ramparts -->
  <path d="M120 250 L180 200 L420 200 L480 250 L460 270 L140 270 Z" fill="#44403C"/>
  <!-- Bastions along the sea walls -->
  <circle cx="180" cy="200" r="16" fill="#292524"/>
  <circle cx="300" cy="195" r="18" fill="#292524"/>
  <circle cx="420" cy="200" r="16" fill="#292524"/>
  <!-- Saffron Flag -->
  <line x1="300" y1="195" x2="300" y2="140" stroke="#F59E0B" stroke-width="3"/>
  <path d="M300 140 L350 152 L300 165 Z" fill="#EA580C"/>
  <!-- Maratha Warship (Gurab) in distance -->
  <polygon points="80,260 110,240 100,260" fill="#78350F"/>
  <line x1="95" y1="240" x2="95" y2="215" stroke="#78350F" stroke-width="2"/>
  <polygon points="95,218 80,228 95,238" fill="#FFFDF9"/>
  <!-- Title Badge -->
  <rect x="20" y="20" width="240" height="52" rx="8" fill="#FFFDF9" opacity="0.9" stroke="#E5DBCA"/>
  <text x="32" y="42" font-family="Inter, sans-serif" font-size="14" font-weight="bold" fill="#78350F">Fort Sindhudurg</text>
  <text x="32" y="60" font-family="Inter, sans-serif" font-size="11" fill="#92400E">Father of the Indian Navy · 1664</text>
</svg>"""
    }
}


def deploy_curated_illustrations() -> dict:
    """Deploy curated vector illustration assets and build manifest."""
    ILLUSTRATIONS_DIR.mkdir(parents=True, exist_ok=True)
    deployed = []

    for key, data in CURATED_ASSETS.items():
        file_path = ILLUSTRATIONS_DIR / data["filename"]
        file_path.write_text(data["svg"], encoding="utf-8")
        deployed.append({
            "key": key,
            "lesson_id": data["lesson_id"],
            "lesson_title": data["lesson_title"],
            "url": f"/illustrations/history/{data['filename']}",
            "title": data["title"],
            "caption": data["caption"]
        })

    # Write manifest
    manifest_data = {
        "version": "1.0",
        "description": "Curated local visual storytelling illustrations for History Learning Hub",
        "illustrations": deployed,
        "hardware_evaluated": check_hardware_feasibility()
    }
    MANIFEST_PATH.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
    return manifest_data


if __name__ == "__main__":
    print("=" * 60)
    print("  HISTORY ILLUSTRATION ENGINE & FEASIBILITY CHECK")
    print("=" * 60)
    feasibility = check_hardware_feasibility()
    print(f"Total RAM:       {feasibility['total_ram_gb']} GB")
    print(f"Free RAM:        {feasibility['free_ram_gb']} GB")
    print(f"Free Disk Space: {feasibility['free_disk_gb']} GB")
    print(f"Feasibility:     {feasibility['recommendation']}")

    res = deploy_curated_illustrations()
    print(f"\n✓ Successfully deployed {len(res['illustrations'])} curated illustrations:")
    for item in res["illustrations"]:
        print(f"  - [{item['lesson_id']}] {item['title']} -> {item['url']}")
    print(f"\n✓ Manifest written to: {MANIFEST_PATH}")
