"""Coder agent for generating code fixes."""

import logging
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from tools.git_tool import GitTool
from models import AgentState, CodeChange

logger = logging.getLogger(__name__)


class CoderAgent:
    """Agent that generates code fixes."""
    
    SYSTEM_PROMPT = """You are an expert software engineer writing code fixes for GitHub issues.

Your task:
1. Analyze the issue and the relevant code files
2. Generate precise code changes to fix the issue
3. Ensure changes are minimal and focused
4. Maintain code style and best practices

CRITICAL RULES:
- STRICT SCOPE CONTROL: Do exactly what the issue asks and NOTHING MORE. Do not refactor, reorganize, or rewrite unrelated code or documentation.
- FORMATTING MATCH: If adding new entries, examples, or code, you MUST rigidly match the format, structure, and syntax of the surrounding file.
- Only modify files that directly fix the issue.
- Keep changes under 300 lines total.
- Preserve existing code style and ensure backwards compatibility.
- VERY IMPORTANT: The code in the ORIGINAL block MUST EXACTLY match the existing code in the file, including all whitespace and indentation!
- NEVER truncate the NEW block. Write out all the code you want to replace the ORIGINAL block with.
- For Markdown (.md) or configuration files, if you want to rewrite the entire file, leave the ORIGINAL block completely empty and put the full new content in the NEW block.

Output format for EACH file to modify:
FILE: <file_path>
EXPLANATION: <one line explaining the change>
ORIGINAL:
<exact original code to be replaced>
NEW:
<new code to replace it>
---

If no changes needed, output: NO_CHANGES_NEEDED
"""
    
    def __init__(self, api_key: str, git_tool: GitTool, model_name: str = "gemini-1.5-flash"):
        """
        Initialize coder agent.
        
        Args:
            api_key: Gemini, OpenAI, Anthropic, or Groq API key
            git_tool: Git tool instance
            model_name: Model to use
        """
        import os
        
        # 1. Groq Support (Key starts with gsk_)
        if api_key and api_key.startswith("gsk_"):
            from langchain_groq import ChatGroq
            actual_model = "llama-3.3-70b-specdec" if any(x in model_name.lower() for x in ["gemini", "gpt", "claude"]) else model_name
            self.llm = ChatGroq(
                model=actual_model,
                groq_api_key=api_key,
                temperature=0.2,
            )
            
        # 2. Anthropic (Claude) Support (Key starts with sk-ant-)
        elif api_key and api_key.startswith("sk-ant-"):
            from langchain_anthropic import ChatAnthropic
            actual_model = "claude-3-5-sonnet-latest" if any(x in model_name.lower() for x in ["gemini", "gpt", "llama"]) else model_name
            self.llm = ChatAnthropic(
                model=actual_model,
                api_key=api_key,
                temperature=0.2,
            )
            
        # 3. OpenRouter Support (Key starts with sk-or-)
        elif api_key and api_key.startswith("sk-or-"):
            from langchain_openai import ChatOpenAI
            base_url = "https://openrouter.ai/api/v1"
            actual_model = model_name
            if "gemini-2.5-flash" in model_name:
                actual_model = "google/gemini-2.5-flash"
            elif "gemini-1.5-flash" in model_name:
                actual_model = "google/gemini-1.5-flash"
            elif "gemini-2.5-pro" in model_name:
                actual_model = "google/gemini-2.5-pro"
            elif "gemini-1.5-pro" in model_name:
                actual_model = "google/gemini-1.5-pro"
            elif "/" not in model_name:
                actual_model = "google/gemini-2.5-flash"
            
            self.llm = ChatOpenAI(
                model=actual_model,
                api_key=api_key,
                base_url=base_url,
                temperature=0.2,
                max_tokens=4096,
            )

        # 3.5. OpenAI / Custom Endpoint Support (Key starts with sk-)
        elif api_key and api_key.startswith("sk-"):
            from langchain_openai import ChatOpenAI
            base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE") or None
            actual_model = "gpt-4o-mini" if any(x in model_name.lower() for x in ["gemini", "llama", "claude"]) else model_name
            self.llm = ChatOpenAI(
                model=actual_model,
                api_key=api_key,
                base_url=base_url,
                temperature=0.2,
            )
            
        # 4. Standard Gemini Fallback
        else:
            self.llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=0.2,
            )
        
        self.git_tool = git_tool
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            ("user", """Repository: {repo_name}
Issue #{issue_number}: {issue_title}

Issue Description:
{issue_body}

Strategy:
{strategy}

Relevant Files:
{files_content}

Generate code changes to fix this issue."""),
        ])
        
        self.chain = self.prompt | self.llm
        
        logger.info(f"Coder agent initialized with model: {model_name}")
    
    def code(self, state: AgentState) -> AgentState:
        """
        Generate code changes.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with code changes
        """
        logger.info("Generating code changes")
        
        if not state.relevant_files:
            logger.error("No relevant files available")
            state.error = "No relevant files from searcher"
            return state
        
        try:
            files_content = self._prepare_files_content(state)
            
            response = self.chain.invoke({
                "repo_name": f"{state.owner}/{state.repo}",
                "issue_number": state.issue_number,
                "issue_title": state.issue.title,
                "issue_body": state.issue.body,
                "strategy": state.strategy,
                "files_content": files_content,
            })
            
            content = response.content
            
            if "NO_CHANGES_NEEDED" in content:
                logger.warning("No changes generated")
                state.error = "Agent determined no changes are needed"
                return state
            
            changes = self._parse_changes(content)
            
            if not changes:
                logger.error("Failed to parse any changes")
                state.error = "Failed to parse code changes from LLM response"
                return state
            
            branch_name = f"ai-fix/issue-{state.issue_number}"
            self.git_tool.create_branch(Path(state.repo_path), branch_name)
            
            for change in changes:
                file_content = self.git_tool.get_file_content(Path(state.repo_path), change.file_path)
                
                if file_content is not None:
                    orig = change.original_content
                    new_val = change.new_content
                    
                    if orig and orig in file_content:
                        updated_content = file_content.replace(orig, new_val)
                        self.git_tool.write_file(Path(state.repo_path), change.file_path, updated_content)
                        logger.info(f"Successfully applied exact patch to {change.file_path}")
                    elif orig and orig.strip() in file_content:
                        updated_content = file_content.replace(orig.strip(), new_val.strip())
                        self.git_tool.write_file(Path(state.repo_path), change.file_path, updated_content)
                        logger.info(f"Successfully applied stripped patch to {change.file_path}")
                    else:
                        is_md = change.file_path.lower().endswith('.md')
                        # Fallback: if we can't find original, only overwrite if orig is empty, file is tiny, or it is a markdown file
                        if not orig.strip() or len(file_content) < 200 or is_md:
                            logger.warning(f"Original block empty, file tiny, or is markdown for {change.file_path}. Falling back to overwrite.")
                            self.git_tool.write_file(Path(state.repo_path), change.file_path, new_val)
                        else:
                            logger.error(f"Failed to apply patch to {change.file_path}: ORIGINAL block not found in file.")
                            state.error = f"Patch failed for {change.file_path}: ORIGINAL content could not be matched exactly. The agent must rewrite the ORIGINAL block to match the file."
                            return state
                else:
                    # New file
                    self.git_tool.write_file(Path(state.repo_path), change.file_path, change.new_content)
            
            state.changes = changes
            state.branch_name = branch_name
            
            # Store reasoning for UI
            state.reasoning["coder"] = {
                "branch_name": branch_name,
                "changes": [
                    {
                        "file": c.file_path,
                        "explanation": c.explanation,
                        "lines_changed": len(c.new_content.splitlines()) - len(c.original_content.splitlines())
                    }
                    for c in changes
                ]
            }
            
            logger.info(f"Generated {len(changes)} code changes on branch {branch_name}")
            
            return state
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            state.error = f"Code generation failed: {str(e)}"
            return state
    
    def _prepare_files_content(self, state: AgentState) -> str:
        """Prepare file contents for LLM prompt with smart truncation to preserve token budget."""
        content_parts = []
        
        # Limit to top 3 files instead of 5 to avoid prompt bloat
        for result in state.relevant_files[:3]:
            file_path = result.file_path
            full_content = self.git_tool.get_file_content(
                Path(state.repo_path),
                file_path,
            )
            
            if not full_content:
                continue
                
            lines = full_content.splitlines()
            total_lines = len(lines)
            
            # Thresholds: 400 lines or 16000 characters
            if total_lines <= 400 and len(full_content) <= 16000:
                content_parts.append(f"File: {file_path}\n```\n{full_content}\n```\n")
                continue
                
            # If the file is larger, we perform smart sliding window extraction around the search snippet
            match_idx = -1
            snippet = result.content.strip() if result.content else ""
            
            if snippet:
                # Clean up the snippet for matching. Take the first non-empty line of the snippet
                snippet_lines = [l.strip() for l in snippet.splitlines() if l.strip()]
                target = snippet_lines[0] if snippet_lines else ""
                
                if len(target) >= 6:  # Only look for significant matches
                    for idx, line in enumerate(lines):
                        if target.lower() in line.lower():
                            match_idx = idx
                            break
                            
            if match_idx != -1:
                # Extract a +/- 100 line window around the match
                start_idx = max(0, match_idx - 100)
                end_idx = min(total_lines, match_idx + 100)
                
                truncated_lines = []
                if start_idx > 0:
                    truncated_lines.append(f"// ... [TRUNCATED: Showing lines {start_idx + 1} to {end_idx} of {total_lines}. Preceding {start_idx} lines omitted to keep prompt size small] ...")
                    
                truncated_lines.extend(lines[start_idx:end_idx])
                
                if end_idx < total_lines:
                    truncated_lines.append(f"// ... [TRUNCATED: Showing lines {start_idx + 1} to {end_idx} of {total_lines}. Remaining {total_lines - end_idx} lines omitted to keep prompt size small] ...")
                    
                truncated_content = "\n".join(truncated_lines)
                logger.info(f"Smart truncated file '{file_path}' to lines {start_idx+1}-{end_idx} around search match (line {match_idx+1}).")
            else:
                # Fallback: Extract first 350 lines
                limit = min(350, total_lines)
                truncated_lines = lines[:limit]
                if total_lines > limit:
                    truncated_lines.append(f"// ... [TRUNCATED: File is too large ({total_lines} lines). First {limit} lines shown to keep prompt size small] ...")
                truncated_content = "\n".join(truncated_lines)
                logger.info(f"File '{file_path}' too large and no clear search match found. Showing first {limit} lines.")
                
            content_parts.append(f"File: {file_path} (Truncated)\n```\n{truncated_content}\n```\n")
            
        return "\n".join(content_parts)

    
    def _parse_changes(self, content: str) -> list[CodeChange]:
        """Parse code changes from LLM response."""
        changes = []
        sections = content.split("---")
        
        for section in sections:
            if not section.strip():
                continue
            
            try:
                file_path = self._extract_field(section, "FILE:")
                explanation = self._extract_field(section, "EXPLANATION:")
                original = self._extract_code_block(section, "ORIGINAL:")
                new = self._extract_code_block(section, "NEW:")
                
                if file_path and new:
                    changes.append(CodeChange(
                        file_path=file_path,
                        original_content=original,
                        new_content=new,
                        explanation=explanation or "Code fix",
                    ))
                    
            except Exception as e:
                logger.warning(f"Failed to parse change section: {e}")
                continue
        
        return changes
    
    def _extract_field(self, content: str, marker: str) -> str:
        """Extract single-line field from content."""
        for line in content.split("\n"):
            if marker in line:
                return line.replace(marker, "").strip()
        return ""
    
    def _extract_code_block(self, content: str, marker: str) -> str:
        """Extract code block from content."""
        lines = content.split("\n")
        result = []
        capturing = False
        
        for line in lines:
            if marker in line:
                capturing = True
                continue
            elif capturing:
                if line.strip() in ["FILE:", "EXPLANATION:", "ORIGINAL:", "NEW:", "---"]:
                    break
                result.append(line)
        
        # Don't strip leading/trailing spaces as it breaks indentation matching
        code = "\n".join(result).strip("\r\n")
        
        # Remove markdown code block backticks if present
        if code.startswith("```"):
            lines = code.split("\n")
            if len(lines) > 1:
                code = "\n".join(lines[1:])
            else:
                code = ""
        
        if code.endswith("```"):
            lines = code.split("\n")
            if len(lines) > 1:
                code = "\n".join(lines[:-1])
            else:
                code = ""
                
        # Only strip newlines again, preserve horizontal whitespace
        return code.strip("\r\n")
