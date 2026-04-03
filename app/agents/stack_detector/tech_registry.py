"""
Technology Registry for StackDetector.
Centralized source of truth for tech classification and metadata.
"""

from typing import Any, Dict

TECH_REGISTRY: Dict[str, Dict[str, Any]] = {
    # Frontend Frameworks
    "react": {
        "name": "React",
        "category": "frontend_framework",
        "type": "framework",
        "scope": "frontend",
    },
    "vue": {
        "name": "Vue",
        "category": "frontend_framework",
        "type": "framework",
        "scope": "frontend",
    },
    "angular": {
        "name": "Angular",
        "category": "frontend_framework",
        "type": "framework",
        "scope": "frontend",
    },
    "nextjs": {
        "name": "Next.js",
        "category": "frontend_framework",
        "type": "framework",
        "scope": "frontend",
    },
    "svelte": {
        "name": "Svelte",
        "category": "frontend_framework",
        "type": "framework",
        "scope": "frontend",
    },
    "tailwind": {
        "name": "Tailwind",
        "category": "frontend_framework",
        "type": "framework",
        "scope": "frontend",
    },
    "vite": {
        "name": "Vite",
        "category": "frontend_framework",
        "type": "framework",
        "scope": "frontend",
    },
    "astro": {
        "name": "Astro",
        "category": "frontend_framework",
        "type": "framework",
        "scope": "frontend",
    },
    # Backend Frameworks
    "fastapi": {
        "name": "FastAPI",
        "category": "backend_framework",
        "type": "framework",
        "scope": "backend",
    },
    "django": {
        "name": "Django",
        "category": "backend_framework",
        "type": "framework",
        "scope": "backend",
    },
    "flask": {
        "name": "Flask",
        "category": "backend_framework",
        "type": "framework",
        "scope": "backend",
    },
    "express": {
        "name": "Express",
        "category": "backend_framework",
        "type": "framework",
        "scope": "backend",
    },
    "nestjs": {
        "name": "NestJS",
        "category": "backend_framework",
        "type": "framework",
        "scope": "backend",
    },
    "laravel": {
        "name": "Laravel",
        "category": "backend_framework",
        "type": "framework",
        "scope": "backend",
    },
    "tauri": {
        "name": "Tauri",
        "category": "backend_framework",
        "type": "framework",
        "scope": "desktop",
    },
    # Languages & Runtimes (Not Frameworks)
    "python": {
        "name": "Python",
        "category": "language",
        "type": "language",
        "scope": "backend",
    },
    "rust": {
        "name": "Rust",
        "category": "language",
        "type": "language",
        "scope": "backend",
    },
    "dart": {
        "name": "Dart",
        "category": "language",
        "type": "language",
        "scope": "mobile",
    },
    "kotlin": {
        "name": "Kotlin",
        "category": "language",
        "type": "language",
        "scope": "mobile",
    },
    "swift": {
        "name": "Swift",
        "category": "language",
        "type": "language",
        "scope": "mobile",
    },
    "objective-c": {
        "name": "Objective-C",
        "category": "language",
        "type": "language",
        "scope": "mobile",
    },
    "objectivec": {
        "name": "Objective-C",
        "category": "language",
        "type": "language",
        "scope": "mobile",
    },
    "java": {
        "name": "Java",
        "category": "language",
        "type": "language",
        "scope": "backend",
    },
    "javascript": {
        "name": "JavaScript",
        "category": "language",
        "type": "language",
        "scope": "frontend",
    },
    "typescript": {
        "name": "TypeScript",
        "category": "language",
        "type": "language",
        "scope": "frontend",
    },
    "bash": {
        "name": "Bash",
        "category": "language",
        "type": "language",
        "scope": "other",
    },
    "c": {
        "name": "C",
        "category": "language",
        "type": "language",
        "scope": "other",
    },
    "cplusplus": {
        "name": "C++",
        "category": "language",
        "type": "language",
        "scope": "other",
    },
    "matlab": {
        "name": "Matlab",
        "category": "language",
        "type": "language",
        "scope": "other",
    },
    "php": {
        "name": "PHP",
        "category": "language",
        "type": "language",
        "scope": "backend",
    },
    "ruby": {
        "name": "Ruby",
        "category": "language",
        "type": "language",
        "scope": "backend",
    },
    "go": {
        "name": "Go",
        "category": "language",
        "type": "language",
        "scope": "backend",
    },
    # Mobile Frameworks
    "flutter": {
        "name": "Flutter",
        "category": "frontend_framework",
        "type": "framework",
        "scope": "mobile",
    },
    "reactnative": {
        "name": "React Native",
        "category": "frontend_framework",
        "type": "framework",
        "scope": "mobile",
    },
    "expo": {
        "name": "Expo",
        "category": "frontend_framework",
        "type": "framework",
        "scope": "mobile",
    },
    # Databases
    "postgresql": {
        "name": "PostgreSQL",
        "category": "database",
        "type": "service",
        "scope": "backend",
    },
    "mysql": {
        "name": "MySQL",
        "category": "database",
        "type": "service",
        "scope": "backend",
    },
    "mongodb": {
        "name": "MongoDB",
        "category": "database",
        "type": "service",
        "scope": "backend",
    },
    "sqlite": {
        "name": "SQLite",
        "category": "database",
        "type": "service",
        "scope": "backend",
    },
    "supabase": {
        "name": "Supabase",
        "category": "database",
        "type": "service",
        "scope": "backend",
    },
    "firebase": {
        "name": "Firebase",
        "category": "database",
        "type": "service",
        "scope": "backend",
    },
    # Caching
    "redis": {
        "name": "Redis",
        "category": "cache",
        "type": "service",
        "scope": "backend",
    },
    "memcached": {
        "name": "Memcached",
        "category": "cache",
        "type": "service",
        "scope": "backend",
    },
    # Infrastructure & Devops
    "docker": {
        "name": "Docker",
        "category": "container",
        "type": "infra",
        "scope": "other",
    },
    "githubactions": {
        "name": "GitHub Actions",
        "category": "ci_cd",
        "type": "infra",
        "scope": "other",
    },
    "kubernetes": {
        "name": "Kubernetes",
        "category": "container",
        "type": "infra",
        "scope": "other",
    },
    "terraform": {
        "name": "Terraform",
        "category": "iac",
        "type": "infra",
        "scope": "other",
    },
    "aws": {
        "name": "AWS",
        "category": "cloud_provider",
        "type": "infra",
        "scope": "other",
    },
    "gcp": {
        "name": "GCP",
        "category": "cloud_provider",
        "type": "infra",
        "scope": "other",
    },
}
