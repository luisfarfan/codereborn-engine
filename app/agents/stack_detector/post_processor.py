import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set

from app.agents.stack_detector.tech_registry import TECH_REGISTRY
from app.domain.enums import AnalysisScope
from app.models.stack_models import (
    ConfigFileInfo,
    DependencyInfo,
    DockerHints,
    FrameworkInfo,
    InfraHint,
    LanguageInfo,
    MonorepoSignals,
    ServiceInfo,
    StackIntelligenceReport,
    UnknownSignal,
    EntrypointInfo
)


class StackPostProcessor:
    """
    Core logic to enrich and normalize deterministic stack detection.
    Recursive and adaptive to complex repo structures.
    Uses a centralized TECH_REGISTRY for classification.
    Ensures 100% data preservation for downstream agents.
    """

    def process(self, raw_json: str, repo_path: str) -> StackIntelligenceReport:
        """
        Parses raw specfy output and enriches it with recursive heuristics.
        """
        raw_data = json.loads(raw_json)
        repo_dir = Path(repo_path)

        # 1. Recursive Data Extraction (Flattening the tree)
        flattened = self._extract_recursive(raw_data)

        project_name = raw_data.get("name") or repo_dir.name
        all_techs = flattened["techs"]
        all_languages = flattened["languages"]
        all_deps = flattened["dependencies"]

        # 2. Languages mapping
        languages = []
        total_lang_score = sum(all_languages.values()) or 1
        for lang, score in all_languages.items():
            languages.append(LanguageInfo(
                language=lang,
                estimated_percentage=round((score / total_lang_score) * 100, 2)
            ))

        # Sort languages by percentage
        languages.sort(key=lambda x: x.estimated_percentage, reverse=True)
        primary_lang = languages[0].language if languages else "unknown"

        # 3. Frameworks & Services detection from flattened techs
        frameworks = []
        services = []
        infra_hints = []
        unknowns = []

        for tech_id in all_techs:
            tech_data = TECH_REGISTRY.get(tech_id)
            if not tech_data:
                # 100% Preservation: Store unmapped techs as UnknownSignal
                unknowns.append(UnknownSignal(
                    signal=tech_id,
                    description="Unmapped technology or library detected"
                ))
                continue

            name = tech_data["name"]
            category = tech_data["category"]
            tech_type = tech_data["type"]

            if tech_type == "framework":
                frameworks.append(FrameworkInfo(
                    name=name,
                    category=category,
                    confidence_score=1.0
                ))
            elif tech_type == "service":
                services.append(ServiceInfo(
                    name=name,
                    service_type=category,
                    description="Detected in repository structure"
                ))
            elif tech_type == "infra":
                infra_hints.append(InfraHint(
                    signal=name,
                    description=f"Infrastructure signal: {category}"
                ))

        # 4. Dependencies
        dependencies = []
        for dep in all_deps:
            if isinstance(dep, list) and len(dep) >= 2:
                dependencies.append(DependencyInfo(
                    name=dep[1],
                    version=dep[2] if len(dep) > 2 else "latest",
                    dep_type=dep[0]
                ))

        # 5. Docker Hints
        dockerfile = repo_dir.joinpath("Dockerfile").exists()
        is_comp = repo_dir.joinpath("docker-compose.yml").exists()
        is_yaml = repo_dir.joinpath("docker-compose.yaml").exists()
        compose = is_comp or is_yaml
        docker_hints = DockerHints(
            dockerfile_present=dockerfile,
            compose_present=compose,
            services_defined=[tech for tech in all_techs if tech == "docker"]
        )

        # 6. Config files
        config_files = []
        known_configs = [
            "package.json", "pyproject.toml", "Cargo.toml", ".env", "go.mod",
            "bun.lock", "pubspec.yaml"
        ]
        for f in known_configs:
            if repo_dir.joinpath(f).exists():
                config_files.append(ConfigFileInfo(file_path=f, config_type="config"))

        # Manual Heuristic: Flutter induction
        is_flutter = any(f.file_path == "pubspec.yaml" for f in config_files)
        if is_flutter and "flutter" not in [f.name.lower() for f in frameworks]:
            frameworks.append(FrameworkInfo(
                name="Flutter",
                category="frontend_framework",
                confidence_score=1.0
            ))

        # 7. Analysis Scope Heuristic
        scope = self._infer_scope(frameworks, primary_lang)

        # 8. Entrypoints (Basic heuristic)
        entrypoints = []
        main_files = ["main.py", "app.py", "index.ts", "server.js", "app.js"]
        for mf in main_files:
            if repo_dir.joinpath(mf).exists():
                entrypoints.append(EntrypointInfo(file_path=mf, role="main"))

        # 9. Confidence Score
        confidence = self._calculate_confidence(all_techs, all_languages)

        return StackIntelligenceReport(
            stack_summary=f"Project {project_name} uses {primary_lang}",
            project_name=project_name,
            analysis_scope=scope,
            primary_language=primary_lang,
            languages=languages,
            frameworks=frameworks,
            dependencies=dependencies,
            services=services,
            infra_hints=infra_hints,
            docker_hints=docker_hints,
            config_files=config_files,
            entrypoints=entrypoints,
            monorepo_signals=MonorepoSignals(
                is_monorepo=len(raw_data.get("childs", [])) > 2
            ),
            confidence_score=confidence,
            unknowns=unknowns,
            analysis_timestamp=datetime.utcnow(),
            agent_version="2.0.0"
        )

    def _extract_recursive(self, node: Dict[str, Any]) -> Dict[str, Any]:
        techs: Set[str] = set()
        languages: Dict[str, float] = {}
        dependencies: List[List[str]] = []

        for t in node.get("techs", []):
            techs.add(t)

        if node.get("tech"):
            techs.add(node["tech"])

        for lang, score in node.get("languages", {}).items():
            languages[lang] = languages.get(lang, 0) + score

        dependencies.extend(node.get("dependencies", []))

        for child in node.get("childs", []):
            child_data = self._extract_recursive(child)
            techs.update(child_data["techs"])
            for lang, score in child_data["languages"].items():
                languages[lang] = languages.get(lang, 0) + score
            dependencies.extend(child_data["dependencies"])

        return {
            "techs": techs,
            "languages": languages,
            "dependencies": dependencies
        }

    def _infer_scope(self, frameworks: List[FrameworkInfo], primary_lang: str) -> AnalysisScope:
        for f in frameworks:
            reg_entry = TECH_REGISTRY.get(f.name.lower())
            if reg_entry and reg_entry.get("scope") == "mobile":
                return AnalysisScope.MOBILE

        language_mobile_hints = ["dart", "swift", "kotlin", "objective-c"]
        if primary_lang.lower() in language_mobile_hints:
            return AnalysisScope.MOBILE

        categories = [f.category for f in frameworks]
        if "backend_framework" in categories and "frontend_framework" not in categories:
            return AnalysisScope.BACKEND
        if "frontend_framework" in categories and "backend_framework" not in categories:
            return AnalysisScope.FRONTEND

        backend_langs = ["python", "go", "rust", "php", "ruby", "java", "c#"]
        if primary_lang.lower() in backend_langs:
            return AnalysisScope.BACKEND

        return AnalysisScope.OTHER

    def _calculate_confidence(self, techs: Set[str], languages: Dict[str, float]) -> float:
        score = 0.3
        if techs:
            score += 0.4
        if languages:
            score += 0.3
        return min(score, 1.0)
