import ast

from app.repository_analysis.models import (
    CodeSymbol,
    ParsedFile,
)


class PythonFileParser:
    def parse(
        self,
        file_path: str,
        content: str,
    ) -> ParsedFile:
        tree = ast.parse(content)

        lines = content.splitlines()

        imports = self._extract_imports(tree)

        symbols: list[CodeSymbol] = []

        for node in tree.body:
            if isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                symbols.append(
                    self._create_symbol(
                        node=node,
                        symbol_type="function",
                        lines=lines,
                    )
                )

            elif isinstance(node, ast.ClassDef):
                symbols.append(
                    self._create_symbol(
                        node=node,
                        symbol_type="class",
                        lines=lines,
                    )
                )

                symbols.extend(
                    self._extract_methods(
                        node=node,
                        lines=lines,
                    )
                )

        return ParsedFile(
            file_path=file_path,
            language="python",
            content=content,
            imports=imports,
            symbols=symbols,
        )

    def _extract_imports(
        self,
        tree: ast.AST,
    ) -> list[str]:
        imports: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return sorted(set(imports))

    def _extract_methods(
        self,
        node: ast.ClassDef,
        lines: list[str],
    ) -> list[CodeSymbol]:
        methods: list[CodeSymbol] = []

        for child in node.body:
            if isinstance(
                child,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            ):
                methods.append(
                    self._create_symbol(
                        node=child,
                        symbol_type="method",
                        lines=lines,
                        parent_name=node.name,
                    )
                )

        return methods

    def _create_symbol(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
        symbol_type: str,
        lines: list[str],
        parent_name: str | None = None,
    ) -> CodeSymbol:
        start_line = node.lineno
        end_line = node.end_lineno or node.lineno

        content = "\n".join(lines[start_line - 1 : end_line])

        return CodeSymbol(
            name=node.name,
            symbol_type=symbol_type,
            start_line=start_line,
            end_line=end_line,
            content=content,
            parent_name=parent_name,
        )
