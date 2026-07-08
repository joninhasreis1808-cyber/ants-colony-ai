"""Orquestrador da App Factory — ponto de entrada único do pipeline.

Encadeia analisar → sugerir → projetar → template → gerar → testar →
corrigir → documentar → (deploy). Mantém um registro dos projetos criados
para consulta posterior.
"""
from __future__ import annotations

from backend.app_factory.architect import SoftwareArchitect
from backend.app_factory.code_generator import CodeGenerator
from backend.app_factory.deployer import AutoDeployer
from backend.app_factory.documenter import AutoDocumenter
from backend.app_factory.enums import DeployTarget
from backend.app_factory.quality_analyzer import QualityAnalyzer
from backend.app_factory.requirement_analyzer import RequirementAnalyzer
from backend.app_factory.results import AppCreationResult, AppOptions
from backend.app_factory.template_engine import TemplateEngine
from backend.app_factory.tester import AutomatedTester


class FactoryOrchestrator:
    """Coordena todos os módulos para criar um app ponta a ponta."""

    def __init__(self) -> None:
        self.analyzer = RequirementAnalyzer()
        self.architect = SoftwareArchitect()
        self.engine = TemplateEngine()
        self.generator = CodeGenerator(self.engine)
        self.tester = AutomatedTester()
        self.documenter = AutoDocumenter()
        self.deployer = AutoDeployer()
        self.quality = QualityAnalyzer()
        self._projects: dict[str, AppCreationResult] = {}

    def create_app(
        self, description: str, options: AppOptions | None = None
    ) -> AppCreationResult:
        """Executa o pipeline completo de criação de app."""
        opts = options or AppOptions()
        requirements = self.analyzer.analyze(description)
        suggestions = self.analyzer.suggest_improvements(requirements)
        architecture = self.architect.design(requirements)
        project = self.generator.generate(architecture, requirements)

        test_report = None
        if opts.run_tests:
            test_report = self.tester.run_tests(project)
            if not test_report.ok:
                project = self.tester.auto_fix(project, test_report)
                test_report = self.tester.run_tests(project)

        readme = ""
        if opts.generate_docs:
            readme = self.documenter.generate_readme(project)
            project.files.setdefault("README.md", readme)

        deploy = None
        if opts.auto_deploy and opts.target:
            deploy = self.deployer.deploy(project, opts.target)

        # Controle de qualidade da colônia: score de maturidade + segurança.
        quality = self.quality.analyze(project).to_dict()

        result = AppCreationResult(
            project=project, requirements=requirements,
            architecture=architecture, test_report=test_report,
            deploy=deploy, readme=readme, suggestions=suggestions,
            quality=quality,
        )
        self._projects[project.id] = result
        return result

    def quick_create(self, description: str) -> AppCreationResult:
        """Pipeline rápido para protótipos (sem testes extensos nem deploy)."""
        return self.create_app(
            description,
            AppOptions(run_tests=False, generate_docs=True,
                       sandbox_test=False, auto_deploy=False),
        )

    def create_from_template(
        self, template_name: str, variables: dict
    ) -> AppCreationResult:
        """Cria diretamente a partir de um template, sem análise de NL."""
        description = f"projeto {template_name}"
        requirements = self.analyzer.analyze(description)
        # Força o tipo pelo template pedido.
        template = self.engine.get_template(template_name)
        rendered = self.engine.render(template, variables)
        from backend.app_factory.schemas import GeneratedProject

        project = GeneratedProject(project_type=requirements.project_type)
        for path, content in rendered.items():
            (project.tests if "test" in path else project.files)[path] = content
        architecture = self.architect.design(requirements)
        result = AppCreationResult(
            project=project, requirements=requirements,
            architecture=architecture,
            readme=self.documenter.generate_readme(project),
        )
        self._projects[project.id] = result
        return result

    def deploy_project(
        self, project_id: str, target: DeployTarget
    ) -> AppCreationResult | None:
        """Faz deploy de um projeto já criado."""
        result = self._projects.get(project_id)
        if result is None:
            return None
        result.deploy = self.deployer.deploy(result.project, target)
        return result

    def get_project_status(self, project_id: str) -> dict | None:
        """Resumo de status de um projeto."""
        result = self._projects.get(project_id)
        return result.summary() if result else None

    def list_projects(self) -> list[dict]:
        """Lista os projetos criados nesta sessão."""
        return [r.summary() for r in self._projects.values()]
